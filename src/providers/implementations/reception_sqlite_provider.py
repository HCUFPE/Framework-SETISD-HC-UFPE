"""Provider SQLAlchemy assíncrono para estado local das operações da Recepção."""

import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.ap_reception import (
    ApCaso,
    ApConferenciaRecebimento,
    ApDevolucao,
    ApExameIhq,
    ApHistoricoCaso,
    ApItemMaterial,
    ApNaoConformidade,
    ApSolicitacao,
)
from ..interfaces.reception_provider_interface import ReceptionProviderInterface


_RELACOES_CASO = {
    "solicitacao",
    "conferencia",
    "materiais",
    "ihqs",
    "naoConformidades",
    "devolucoes",
    "historico",
}


def _dump(value: Any) -> str:
    """Serializa os payloads camelCase armazenados no banco local."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)


def _load(value: str) -> dict[str, Any]:
    """Desserializa um objeto de domínio."""
    return json.loads(value)


class ReceptionSqliteProvider(ReceptionProviderInterface):
    """Persistência APP_DB; os controllers não dependem do ORM concreto."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def seed_demo_state(self, estado: dict[str, Any]) -> None:
        """Restaura idempotentemente a carga AP que já existia no mock do frontend."""
        for solicitacao in estado["solicitacoes"]:
            codigo = str(solicitacao["codigoSolicitacao"]).strip().upper()
            registro = await self.session.get(ApSolicitacao, codigo)
            if registro is None:
                self.session.add(ApSolicitacao(
                    codigo_solicitacao=codigo,
                    situacao_recepcao=solicitacao["situacaoRecepcao"],
                    data_solicitacao=solicitacao["dataSolicitacao"],
                    caso_numero=solicitacao.get("casoNumero"),
                    ihq_codigo=solicitacao.get("ihqCodigo"),
                    ihq_caso_numero=solicitacao.get("ihqCasoNumero"),
                    devolucao_id=solicitacao.get("devolucaoId"),
                    payload=_dump(solicitacao),
                ))
            elif await self._pode_substituir_placeholder(registro):
                registro.situacao_recepcao = solicitacao["situacaoRecepcao"]
                registro.data_solicitacao = solicitacao["dataSolicitacao"]
                registro.caso_numero = solicitacao.get("casoNumero")
                registro.ihq_codigo = solicitacao.get("ihqCodigo")
                registro.ihq_caso_numero = solicitacao.get("ihqCasoNumero")
                registro.devolucao_id = solicitacao.get("devolucaoId")
                registro.payload = _dump(solicitacao)

        await self.session.flush()

        for caso in estado["casos"]:
            numero = str(caso["numeroInterno"]).strip().upper()
            if await self.session.get(ApCaso, numero) is not None:
                continue
            await self.salvar_caso(caso)
            await self.adicionar_materiais(numero, caso.get("materiais", []))
            for ihq in caso.get("ihqs", []):
                codigo_ihq = ihq["codigoInternoIhq"]
                if await self.session.get(ApExameIhq, codigo_ihq) is None:
                    self.session.add(ApExameIhq(
                        codigo_interno=codigo_ihq,
                        caso_numero=numero,
                        solicitacao_codigo=ihq["solicitacaoAghuCodigo"],
                        payload=_dump(ihq),
                    ))
            for evento in caso.get("historico", []):
                await self.adicionar_historico(numero, evento)

        for conferencia in estado["conferencias"]:
            if await self.session.get(ApConferenciaRecebimento, conferencia["id"]) is None:
                await self.adicionar_conferencia(conferencia)

        for nao_conformidade in estado["naoConformidades"]:
            if await self.session.get(ApNaoConformidade, nao_conformidade["id"]) is None:
                await self.adicionar_nao_conformidade(nao_conformidade)

        for devolucao in estado["devolucoes"]:
            if await self.session.get(ApDevolucao, devolucao["id"]) is None:
                await self.adicionar_devolucao(devolucao)

        await self.session.commit()

    async def _pode_substituir_placeholder(self, registro: ApSolicitacao) -> bool:
        """Atualiza apenas os placeholders recém-criados e ainda sem uso no AP local."""
        if registro.situacao_recepcao != "AGUARDANDO_RECEBIMENTO":
            return False
        nome = str(_load(registro.payload).get("nomePaciente", "")).upper()
        if not nome.startswith("PACIENTE FICT"):
            return False
        caso = await self.session.execute(
            select(ApCaso.numero_interno).where(ApCaso.solicitacao_codigo == registro.codigo_solicitacao)
        )
        if caso.first() is not None:
            return False
        nao_conformidade = await self.session.execute(
            select(ApNaoConformidade.id).where(
                ApNaoConformidade.solicitacao_codigo == registro.codigo_solicitacao
            )
        )
        return nao_conformidade.first() is None

    async def seed_solicitacoes(self, solicitacoes: list[dict[str, Any]]) -> None:
        """Inclui apenas solicitações que ainda não existem, sem resetar seus estados."""
        valores = [
            {
                "codigo_solicitacao": str(payload["codigoSolicitacao"]).strip().upper(),
                "situacao_recepcao": payload["situacaoRecepcao"],
                "data_solicitacao": payload["dataSolicitacao"],
                "payload": _dump(payload),
            }
            for payload in solicitacoes
        ]
        if valores:
            comando = sqlite_insert(ApSolicitacao).values(valores).on_conflict_do_nothing(
                index_elements=[ApSolicitacao.codigo_solicitacao]
            )
            await self.session.execute(comando)
        await self.session.commit()

    async def buscar_solicitacao(self, codigo: str) -> dict[str, Any] | None:
        """Busca solicitação sem depender da origem configurada."""
        registro = await self.session.get(ApSolicitacao, codigo.strip().upper())
        return self._solicitacao_payload(registro) if registro else None

    async def listar_solicitacoes_pendentes(self) -> list[dict[str, Any]]:
        """Lista solicitações pendentes ordenadas pela data de solicitação."""
        resultado = await self.session.execute(
            select(ApSolicitacao)
            .where(ApSolicitacao.situacao_recepcao == "AGUARDANDO_RECEBIMENTO")
            .order_by(ApSolicitacao.data_solicitacao.asc())
        )
        return [self._solicitacao_payload(row) for row in resultado.scalars().all()]

    async def contar_solicitacoes_pendentes(self) -> int:
        """Conta solicitações locais aguardando recebimento."""
        resultado = await self.session.execute(
            select(func.count()).select_from(ApSolicitacao).where(
                ApSolicitacao.situacao_recepcao == "AGUARDANDO_RECEBIMENTO"
            )
        )
        return int(resultado.scalar_one())

    async def salvar_solicitacao(self, payload: dict[str, Any]) -> None:
        """Atualiza os campos de estado local após recebimento ou devolução."""
        codigo = str(payload["codigoSolicitacao"]).strip().upper()
        registro = await self.session.get(ApSolicitacao, codigo)
        if registro is None:
            registro = ApSolicitacao(codigo_solicitacao=codigo, payload="{}", data_solicitacao="")
            self.session.add(registro)
        registro.situacao_recepcao = payload["situacaoRecepcao"]
        registro.data_solicitacao = payload["dataSolicitacao"]
        registro.caso_numero = payload.get("casoNumero")
        registro.ihq_codigo = payload.get("ihqCodigo")
        registro.ihq_caso_numero = payload.get("ihqCasoNumero")
        registro.devolucao_id = payload.get("devolucaoId")
        registro.payload = _dump(payload)
        await self.session.flush()

    async def listar_casos(self) -> list[dict[str, Any]]:
        """Lista agregados persistidos por data de entrada decrescente."""
        resultado = await self.session.execute(select(ApCaso).order_by(ApCaso.data_entrada.desc()))
        return [await self._caso_payload(row) for row in resultado.scalars().all()]

    async def buscar_caso(self, numero: str) -> dict[str, Any] | None:
        """Busca número interno sem diferenciar caixa."""
        registro = await self.session.get(ApCaso, numero.strip().upper())
        return await self._caso_payload(registro) if registro else None

    async def salvar_caso(self, payload: dict[str, Any]) -> None:
        """Insere/atualiza estado base, deixando relações nas tabelas próprias."""
        numero = str(payload["numeroInterno"]).strip().upper()
        solicitacao = payload["solicitacao"]
        registro = await self.session.get(ApCaso, numero)
        if registro is None:
            registro = ApCaso(numero_interno=numero, solicitacao_codigo=solicitacao["codigoSolicitacao"])
            self.session.add(registro)
        registro.solicitacao_codigo = solicitacao["codigoSolicitacao"]
        registro.tipo_exame = payload["tipoExame"]
        registro.status = payload["status"]
        registro.data_entrada = payload["dataEntradaSap"]
        registro.payload = _dump({key: value for key, value in payload.items() if key not in _RELACOES_CASO})
        await self.session.flush()

    async def adicionar_conferencia(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Persiste uma conferência e retorna o identificador gerado."""
        registro = ApConferenciaRecebimento(
            id=payload.get("id"),
            solicitacao_codigo=payload["solicitacaoCodigo"],
            caso_numero=payload.get("casoNumero"),
            resultado=payload["resultado"],
            conferido_em=payload["conferidoEm"],
            payload=_dump({key: value for key, value in payload.items() if key != "id"}),
        )
        self.session.add(registro)
        await self.session.flush()
        return {**payload, "id": registro.id}

    async def adicionar_materiais(self, caso_numero: str, materiais: list[dict[str, Any]]) -> None:
        """Persiste árvore dos itens da Recepção sem criar registros de etapas futuras."""

        def adicionar(item: dict[str, Any], codigo_pai: str | None = None) -> None:
            filhos = item.get("filhos", [])
            self.session.add(
                ApItemMaterial(
                    codigo=item["codigo"],
                    caso_numero=caso_numero,
                    codigo_pai=codigo_pai,
                    payload=_dump({key: value for key, value in item.items() if key != "filhos"}),
                )
            )
            for filho in filhos:
                adicionar(filho, item["codigo"])

        for material in materiais:
            adicionar(material)
        await self.session.flush()

    async def adicionar_historico(self, caso_numero: str, evento: dict[str, Any]) -> dict[str, Any]:
        """Acrescenta evento imutável e retorna seu identificador."""
        registro = ApHistoricoCaso(
            caso_numero=caso_numero,
            ocorrido_em=evento["ocorridoEm"],
            payload=_dump({key: value for key, value in evento.items() if key != "id"}),
        )
        self.session.add(registro)
        await self.session.flush()
        return {**evento, "id": registro.id}

    async def adicionar_nao_conformidade(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Insere a não conformidade associada à solicitação/caso quando aplicável."""
        registro = ApNaoConformidade(
            id=payload.get("id"),
            caso_numero=payload.get("casoNumero"),
            solicitacao_codigo=payload.get("solicitacaoCodigo"),
            status=payload["status"],
            payload=_dump({key: value for key, value in payload.items() if key != "id"}),
        )
        self.session.add(registro)
        await self.session.flush()
        return {**payload, "id": registro.id}

    async def adicionar_devolucao(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Insere devolução vinculada à não conformidade correspondente."""
        registro = ApDevolucao(
            id=payload.get("id"),
            nao_conformidade_id=payload["naoConformidadeId"],
            caso_numero=payload.get("casoNumero"),
            solicitacao_codigo=payload.get("solicitacaoCodigo"),
            situacao=payload["situacao"],
            devolvida_em=payload["devolvidaEm"],
            payload=_dump({key: value for key, value in payload.items() if key != "id"}),
        )
        self.session.add(registro)
        await self.session.flush()
        return {**payload, "id": registro.id}

    async def listar_devolucoes(self) -> list[dict[str, Any]]:
        """Lista devoluções detalhadas em ordem cronológica decrescente."""
        resultado = await self.session.execute(select(ApDevolucao).order_by(ApDevolucao.devolvida_em.desc()))
        devolucoes: list[dict[str, Any]] = []
        for devolucao in resultado.scalars().all():
            nc = await self.session.get(ApNaoConformidade, devolucao.nao_conformidade_id)
            if nc is None:
                continue
            payload = _load(devolucao.payload)
            payload["id"] = devolucao.id
            nc_payload = _load(nc.payload)
            nc_payload["id"] = nc.id
            devolucoes.append({**payload, "naoConformidade": nc_payload, "rejeicaoNaRecepcao": not bool(devolucao.caso_numero)})
        return devolucoes

    async def atualizar_situacao_devolucao(self, devolucao_id: int, situacao: str) -> dict[str, Any] | None:
        """Atualiza devolução e não conformidade associada na sessão corrente."""
        devolucao = await self.session.get(ApDevolucao, devolucao_id)
        if devolucao is None:
            return None
        nc = await self.session.get(ApNaoConformidade, devolucao.nao_conformidade_id)
        if nc is None:
            return None

        payload = _load(devolucao.payload)
        nc_payload = _load(nc.payload)
        anterior = {
            **payload,
            "id": devolucao.id,
            "situacao": devolucao.situacao,
            "naoConformidade": {**nc_payload, "id": nc.id, "status": nc.status},
            "rejeicaoNaRecepcao": not bool(devolucao.caso_numero),
        }
        status_nc_anterior = nc.status
        if devolucao.situacao == situacao:
            return {
                "anterior": anterior,
                "atual": anterior,
                "statusNaoConformidadeAnterior": status_nc_anterior,
                "statusNaoConformidadeAtual": status_nc_anterior,
            }

        devolucao.situacao = situacao
        payload["situacao"] = situacao
        devolucao.payload = _dump(payload)
        nc.status = "RESOLVIDA" if situacao in {"NOVA_AMOSTRA_RECEBIDA", "ENCERRADA"} else "ABERTA"
        nc_payload["status"] = nc.status
        nc.payload = _dump(nc_payload)
        await self.session.flush()

        atual = {
            **payload,
            "id": devolucao.id,
            "situacao": devolucao.situacao,
            "naoConformidade": {**nc_payload, "id": nc.id, "status": nc.status},
            "rejeicaoNaRecepcao": not bool(devolucao.caso_numero),
        }
        return {
            "anterior": anterior,
            "atual": atual,
            "statusNaoConformidadeAnterior": status_nc_anterior,
            "statusNaoConformidadeAtual": nc.status,
        }

    def _solicitacao_payload(self, registro: ApSolicitacao) -> dict[str, Any]:
        """Monta solicitação com os campos locais de estado como fonte oficial."""
        payload = _load(registro.payload)
        payload["codigoSolicitacao"] = registro.codigo_solicitacao
        payload["situacaoRecepcao"] = registro.situacao_recepcao
        payload["dataSolicitacao"] = registro.data_solicitacao
        payload["casoNumero"] = registro.caso_numero
        payload["ihqCodigo"] = registro.ihq_codigo
        payload["ihqCasoNumero"] = registro.ihq_caso_numero
        payload["devolucaoId"] = registro.devolucao_id
        return {key: value for key, value in payload.items() if value is not None}

    async def _caso_payload(self, registro: ApCaso) -> dict[str, Any]:
        """Carrega relações persistidas e mantém o shape CasoAp usado pelo Vue."""
        payload = _load(registro.payload)
        solicitacao = await self.session.get(ApSolicitacao, registro.solicitacao_codigo)
        payload["solicitacao"] = self._solicitacao_payload(solicitacao) if solicitacao else {}

        conf_result = await self.session.execute(
            select(ApConferenciaRecebimento)
            .where(ApConferenciaRecebimento.caso_numero == registro.numero_interno)
            .order_by(ApConferenciaRecebimento.id.desc())
        )
        conferencia = conf_result.scalars().first()
        if conferencia:
            conf_payload = _load(conferencia.payload)
            conf_payload["id"] = conferencia.id
            payload["conferencia"] = conf_payload
        else:
            payload["conferencia"] = None

        material_result = await self.session.execute(
            select(ApItemMaterial).where(ApItemMaterial.caso_numero == registro.numero_interno)
        )
        material_rows = material_result.scalars().all()
        materiais: dict[str, dict[str, Any]] = {}
        for item in material_rows:
            data = _load(item.payload)
            data.update({"codigo": item.codigo, "filhos": []})
            materiais[item.codigo] = data
        raizes: list[dict[str, Any]] = []
        for item in material_rows:
            if item.codigo_pai and item.codigo_pai in materiais:
                materiais[item.codigo_pai]["filhos"].append(materiais[item.codigo])
            else:
                raizes.append(materiais[item.codigo])
        payload["materiais"] = raizes

        ihq_result = await self.session.execute(
            select(ApExameIhq).where(ApExameIhq.caso_numero == registro.numero_interno)
        )
        ihqs: list[dict[str, Any]] = []
        for ihq in ihq_result.scalars().all():
            ihq_payload = _load(ihq.payload)
            ihq_payload["codigoInternoIhq"] = ihq.codigo_interno
            ihqs.append(ihq_payload)
        payload["ihqs"] = ihqs

        nc_result = await self.session.execute(
            select(ApNaoConformidade).where(ApNaoConformidade.caso_numero == registro.numero_interno)
        )
        nao_conformidades: list[dict[str, Any]] = []
        for nc in nc_result.scalars().all():
            nc_payload = _load(nc.payload)
            nc_payload["id"] = nc.id
            nc_payload["status"] = nc.status
            nao_conformidades.append(nc_payload)
        payload["naoConformidades"] = nao_conformidades

        devolucoes_result = await self.session.execute(
            select(ApDevolucao).where(ApDevolucao.caso_numero == registro.numero_interno)
        )
        devolucoes: list[dict[str, Any]] = []
        for devolucao in devolucoes_result.scalars().all():
            devolucao_payload = _load(devolucao.payload)
            devolucao_payload.update({"id": devolucao.id, "situacao": devolucao.situacao})
            devolucoes.append(devolucao_payload)
        payload["devolucoes"] = devolucoes

        historico_result = await self.session.execute(
            select(ApHistoricoCaso)
            .where(ApHistoricoCaso.caso_numero == registro.numero_interno)
            .order_by(ApHistoricoCaso.id.asc())
        )
        historico: list[dict[str, Any]] = []
        for evento in historico_result.scalars().all():
            evento_payload = _load(evento.payload)
            evento_payload["id"] = evento.id
            historico.append(evento_payload)
        payload["historico"] = historico
        return payload

