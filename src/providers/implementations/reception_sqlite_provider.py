"""Provider SQLAlchemy assíncrono para estado local das operações da Recepção."""

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

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
    "casoOrigem",
    "casoOrigemNumero",
    "tipoDerivacao",
    "examesDerivados",
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
            tipo = str(solicitacao["tipoExameSugerido"]).strip().upper()
            grupo_id = str(solicitacao.get("id") or f"{codigo}:{tipo}").strip().upper()
            registro = await self.session.get(ApSolicitacao, grupo_id)
            if registro is None:
                self.session.add(ApSolicitacao(
                    id=grupo_id,
                    codigo_solicitacao=codigo,
                    tipo_exame=tipo,
                    situacao_recepcao=solicitacao["situacaoRecepcao"],
                    data_solicitacao=solicitacao["dataSolicitacao"],
                    caso_numero=solicitacao.get("casoNumero"),
                    ihq_codigo=solicitacao.get("ihqCodigo"),
                    ihq_caso_numero=solicitacao.get("ihqCasoNumero"),
                    devolucao_id=solicitacao.get("devolucaoId"),
                    payload=_dump(solicitacao),
                ))
            elif await self._pode_substituir_placeholder(registro):
                registro.codigo_solicitacao = codigo
                registro.tipo_exame = tipo
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
                        solicitacao_id=ihq.get("solicitacaoId") or f"{ihq['solicitacaoAghuCodigo']}:IHQ",
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
            select(ApCaso.numero_interno).where(ApCaso.solicitacao_id == registro.id)
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
                "id": str(payload.get("id") or f"{payload['codigoSolicitacao']}:{payload['tipoExameSugerido']}").strip().upper(),
                "codigo_solicitacao": str(payload["codigoSolicitacao"]).strip().upper(),
                "tipo_exame": str(payload["tipoExameSugerido"]).strip().upper(),
                "situacao_recepcao": payload["situacaoRecepcao"],
                "data_solicitacao": payload["dataSolicitacao"],
                "payload": _dump(payload),
            }
            for payload in solicitacoes
        ]
        if valores:
            comando = sqlite_insert(ApSolicitacao).values(valores).on_conflict_do_nothing(
                index_elements=[ApSolicitacao.id]
            )
            await self.session.execute(comando)
        await self.session.commit()

    async def buscar_solicitacao(self, codigo: str) -> dict[str, Any] | None:
        """Busca um grupo pelo identificador composto, sem depender da origem."""
        registro = await self.session.get(ApSolicitacao, codigo.strip().upper())
        return self._solicitacao_payload(registro) if registro else None

    async def listar_exames_da_solicitacao(self, codigo: str) -> list[dict[str, Any]]:
        """Lista todos os grupos de uma solicitação AGHU."""
        resultado = await self.session.execute(
            select(ApSolicitacao)
            .where(ApSolicitacao.codigo_solicitacao == codigo.strip().upper())
            .order_by(ApSolicitacao.tipo_exame.asc())
        )
        return [self._solicitacao_payload(row) for row in resultado.scalars().all()]

    async def listar_solicitacoes_pendentes(self) -> list[dict[str, Any]]:
        """Lista solicitações pendentes ordenadas pela data de solicitação."""
        resultado = await self.session.execute(
            select(ApSolicitacao)
            .where(ApSolicitacao.situacao_recepcao == "AGUARDANDO_RECEBIMENTO")
            .order_by(ApSolicitacao.data_solicitacao.asc())
        )
        return [self._solicitacao_payload(row) for row in resultado.scalars().all()]

    async def contar_solicitacoes_pendentes(self) -> int:
        """Conta códigos AGHU distintos que ainda têm grupo pendente."""
        resultado = await self.session.execute(
            select(func.count(func.distinct(ApSolicitacao.codigo_solicitacao))).where(
                ApSolicitacao.situacao_recepcao == "AGUARDANDO_RECEBIMENTO"
            )
        )
        return int(resultado.scalar_one())

    async def salvar_solicitacao(self, payload: dict[str, Any]) -> None:
        """Atualiza os campos de estado local após recebimento ou devolução."""
        grupo_id = str(payload.get("id") or f"{payload['codigoSolicitacao']}:{payload['tipoExameSugerido']}").strip().upper()
        registro = await self.session.get(ApSolicitacao, grupo_id)
        if registro is None:
            registro = ApSolicitacao(
                id=grupo_id,
                codigo_solicitacao=str(payload["codigoSolicitacao"]).strip().upper(),
                tipo_exame=str(payload["tipoExameSugerido"]).strip().upper(),
                payload="{}",
                data_solicitacao="",
                situacao_recepcao=payload["situacaoRecepcao"],
            )
            self.session.add(registro)
        registro.codigo_solicitacao = str(payload["codigoSolicitacao"]).strip().upper()
        registro.tipo_exame = str(payload["tipoExameSugerido"]).strip().upper()
        registro.situacao_recepcao = payload["situacaoRecepcao"]
        registro.data_solicitacao = payload["dataSolicitacao"]
        registro.caso_numero = payload.get("casoNumero")
        registro.ihq_codigo = payload.get("ihqCodigo")
        registro.ihq_caso_numero = payload.get("ihqCasoNumero")
        registro.devolucao_id = payload.get("devolucaoId")
        registro.payload = _dump(payload)
        await self.session.flush()

    async def cancelar_solicitacao(self, grupo_id: str, cancelamento: dict[str, Any]) -> dict[str, Any] | None:
        """Marca somente grupo ainda pendente; atualização condicional evita corrida de estado."""
        registro = await self.session.get(ApSolicitacao, grupo_id.strip().upper())
        if registro is None or registro.situacao_recepcao != "AGUARDANDO_RECEBIMENTO":
            return None
        payload = _load(registro.payload)
        payload["situacaoRecepcao"] = "CANCELADA"
        payload["cancelamento"] = cancelamento
        resultado = await self.session.execute(
            update(ApSolicitacao)
            .where(
                ApSolicitacao.id == registro.id,
                ApSolicitacao.situacao_recepcao == "AGUARDANDO_RECEBIMENTO",
            )
            .values(situacao_recepcao="CANCELADA", payload=_dump(payload))
        )
        if resultado.rowcount != 1:
            return None
        await self.session.refresh(registro)
        return self._solicitacao_payload(registro)

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
            registro = ApCaso(numero_interno=numero, solicitacao_id=solicitacao["id"])
            self.session.add(registro)
        registro.solicitacao_id = solicitacao["id"]
        registro.caso_origem_numero = payload.get("casoOrigemNumero")
        registro.tipo_derivacao = payload.get("tipoDerivacao")
        registro.tipo_exame = payload["tipoExame"]
        registro.status = payload["status"]
        registro.data_entrada = payload["dataEntradaSap"]
        registro.payload = _dump({key: value for key, value in payload.items() if key not in _RELACOES_CASO})
        await self.session.flush()

    async def adicionar_conferencia(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Persiste uma conferência e retorna o identificador gerado."""
        registro = ApConferenciaRecebimento(
            id=payload.get("id"),
            solicitacao_id=payload["solicitacaoId"],
            solicitacao_codigo=payload["solicitacaoCodigo"],
            caso_numero=payload.get("casoNumero"),
            resultado=payload["resultado"],
            conferido_em=payload["conferidoEm"],
            payload=_dump({key: value for key, value in payload.items() if key != "id"}),
        )
        self.session.add(registro)
        await self.session.flush()
        return {**payload, "id": registro.id}

    async def adicionar_ihq(self, caso_numero: str, solicitacao_id: str, exame: dict[str, Any]) -> None:
        """Persiste vínculo IHQ em sua tabela de domínio."""
        self.session.add(ApExameIhq(
            codigo_interno=exame["codigoInternoIhq"],
            caso_numero=caso_numero,
            solicitacao_id=solicitacao_id,
            payload=_dump(exame),
        ))
        await self.session.flush()

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
            devolucoes.append({
                **payload,
                "casoNumero": devolucao.caso_numero,
                "naoConformidade": nc_payload,
                "rejeicaoNaRecepcao": payload.get("rejeicaoNaRecepcao", not bool(devolucao.caso_numero)),
            })
        return devolucoes

    async def atualizar_situacao_devolucao(self, devolucao_id: int, situacao: str) -> dict[str, Any] | None:
        """Atualiza a devolução e reabre solicitações ou caso na sessão corrente."""
        devolucao = await self.session.get(ApDevolucao, devolucao_id)
        if devolucao is None:
            return None
        nc = await self.session.get(ApNaoConformidade, devolucao.nao_conformidade_id)
        if nc is None:
            return None

        payload = _load(devolucao.payload)
        nc_payload = _load(nc.payload)
        rejeicao_na_recepcao = payload.get("rejeicaoNaRecepcao", devolucao.caso_numero is None)
        anterior = {
            **payload,
            "id": devolucao.id,
            "situacao": devolucao.situacao,
            "naoConformidade": {**nc_payload, "id": nc.id, "status": nc.status},
            "rejeicaoNaRecepcao": rejeicao_na_recepcao,
        }
        status_nc_anterior = nc.status
        if devolucao.situacao == situacao:
            return {
                "anterior": anterior,
                "atual": anterior,
                "statusNaoConformidadeAnterior": status_nc_anterior,
                "statusNaoConformidadeAtual": status_nc_anterior,
            }

        grupos: list[ApSolicitacao] = []
        grupos_anteriores: list[dict[str, Any]] = []
        caso: ApCaso | None = None
        status_caso_anterior: str | None = None
        status_caso_atual: str | None = None

        if situacao == "NOVA_AMOSTRA_RECEBIDA":
            if devolucao.situacao != "AGUARDANDO_NOVA_AMOSTRA":
                raise HTTPException(status_code=409, detail="A devolução não está aguardando nova amostra.")
            if devolucao.caso_numero:
                caso = await self.session.get(ApCaso, devolucao.caso_numero)
                if caso is None or caso.status != "DEVOLVIDO":
                    raise HTTPException(status_code=409, detail="O caso não está no estado devolvido.")
                status_caso_anterior = caso.status
                status_caso_atual = str(nc_payload.get("statusCasoAnterior") or payload.get("statusCasoAnterior") or "RECEBIDO")
                if status_caso_atual in {"DEVOLVIDO", "CANCELADO", "LAUDO_CONCLUIDO", "EM_ARQUIVAMENTO", "ARQUIVADO"}:
                    status_caso_atual = "RECEBIDO"
            else:
                ids_grupos = [str(item).strip().upper() for item in payload.get("solicitacaoIds", [])]
                if not ids_grupos:
                    raise HTTPException(status_code=409, detail="A devolução não possui grupos de solicitação vinculados.")
                for grupo_id in ids_grupos:
                    grupo = await self.session.get(ApSolicitacao, grupo_id)
                    if grupo is None or grupo.situacao_recepcao != "DEVOLVIDA" or grupo.devolucao_id != devolucao.id:
                        raise HTTPException(status_code=409, detail="Um grupo vinculado já avançou ou não pertence a esta devolução.")
                    grupos.append(grupo)
                    grupos_anteriores.append(self._solicitacao_payload(grupo))
        elif situacao == "AGUARDANDO_NOVA_AMOSTRA" and devolucao.situacao == "NOVA_AMOSTRA_RECEBIDA":
            if devolucao.caso_numero:
                caso = await self.session.get(ApCaso, devolucao.caso_numero)
                if caso is None or caso.status != "DEVOLVIDO":
                    raise HTTPException(status_code=409, detail="A solicitação vinculada já avançou após a reabertura.")
            else:
                for grupo_id in payload.get("solicitacaoIds", []):
                    grupo = await self.session.get(ApSolicitacao, str(grupo_id).strip().upper())
                    if grupo is None or grupo.situacao_recepcao != "DEVOLVIDA" or grupo.devolucao_id != devolucao.id:
                        raise HTTPException(status_code=409, detail="A solicitação vinculada já avançou após a reabertura.")

        devolucao.situacao = situacao
        payload["situacao"] = situacao
        nc.status = "RESOLVIDA" if situacao in {"NOVA_AMOSTRA_RECEBIDA", "ENCERRADA"} else "ABERTA"
        nc_payload["status"] = nc.status
        nc.payload = _dump(nc_payload)
        grupos_atuais: list[dict[str, Any]] = []

        if situacao == "NOVA_AMOSTRA_RECEBIDA":
            payload["regularizadaEm"] = datetime.now(timezone.utc).isoformat()
            if caso is not None:
                caso.status = status_caso_atual or "RECEBIDO"
            else:
                metadados = {
                    "id": devolucao.id,
                    "situacao": situacao,
                    "devolvidaEm": payload.get("devolvidaEm"),
                    "regularizadaEm": payload["regularizadaEm"],
                    "tipo": nc_payload.get("tipo"),
                    "descricao": nc_payload.get("descricao"),
                    "observacao": nc_payload.get("observacao"),
                    "unidadeOrigem": payload.get("unidadeOrigem"),
                    "rejeicaoNaRecepcao": True,
                }
                metadados = {key: value for key, value in metadados.items() if value is not None}
                payload["rejeicaoNaRecepcao"] = True
                for grupo in grupos:
                    grupo_payload = _load(grupo.payload)
                    grupo_payload["situacaoRecepcao"] = "AGUARDANDO_RECEBIMENTO"
                    grupo_payload.pop("devolucaoId", None)
                    grupo_payload["devolucaoRegularizada"] = metadados
                    grupo.situacao_recepcao = "AGUARDANDO_RECEBIMENTO"
                    grupo.devolucao_id = None
                    grupo.payload = _dump(grupo_payload)
                    grupos_atuais.append(self._solicitacao_payload(grupo))
        devolucao.payload = _dump(payload)
        await self.session.flush()

        atual = {
            **payload,
            "id": devolucao.id,
            "situacao": devolucao.situacao,
            "naoConformidade": {**nc_payload, "id": nc.id, "status": nc.status},
            "rejeicaoNaRecepcao": rejeicao_na_recepcao,
        }
        return {
            "anterior": anterior,
            "atual": atual,
            "statusNaoConformidadeAnterior": status_nc_anterior,
            "statusNaoConformidadeAtual": nc.status,
            "solicitacoesAnteriores": grupos_anteriores,
            "solicitacoesAtuais": grupos_atuais,
            "statusCasoAnterior": status_caso_anterior,
            "statusCasoAtual": status_caso_atual,
        }

    async def associar_ocorrencias_reabertas(self, solicitacao_id: str, caso_numero: str) -> list[dict[str, Any]]:
        """Vincula ao novo caso os registros de rejeição pré-recepção já regularizados."""
        grupo_id = solicitacao_id.strip().upper()
        nc_result = await self.session.execute(select(ApNaoConformidade))
        associadas: list[dict[str, Any]] = []
        for nc in nc_result.scalars().all():
            nc_payload = _load(nc.payload)
            if grupo_id not in [str(item).strip().upper() for item in nc_payload.get("solicitacaoIds", [])]:
                continue
            casos_associados = [str(item).strip().upper() for item in nc_payload.get("casoNumeros", [])]
            if caso_numero.strip().upper() in casos_associados:
                continue
            devolucoes_result = await self.session.execute(
                select(ApDevolucao).where(ApDevolucao.nao_conformidade_id == nc.id)
            )
            devolucao = devolucoes_result.scalars().first()
            if devolucao is None:
                continue
            devolucao_payload = _load(devolucao.payload)
            if devolucao.situacao != "NOVA_AMOSTRA_RECEBIDA" or devolucao_payload.get("rejeicaoNaRecepcao") is not True:
                continue
            casos_associados.append(caso_numero)
            nc_payload["casoNumeros"] = casos_associados
            nc.payload = _dump(nc_payload)
            devolucao_payload["casoNumeros"] = casos_associados
            devolucao.payload = _dump(devolucao_payload)
            if nc.caso_numero is None:
                nc.caso_numero = caso_numero
            if devolucao.caso_numero is None:
                devolucao.caso_numero = caso_numero
            associadas.append({
                "devolucaoId": devolucao.id,
                "solicitacaoId": grupo_id,
                "devolvidaEm": devolucao_payload.get("devolvidaEm"),
                "regularizadaEm": devolucao_payload.get("regularizadaEm"),
            })
        await self.session.flush()
        return associadas

    def _solicitacao_payload(self, registro: ApSolicitacao) -> dict[str, Any]:
        """Monta solicitação com os campos locais de estado como fonte oficial."""
        payload = _load(registro.payload)
        payload["id"] = registro.id
        payload["codigoSolicitacao"] = registro.codigo_solicitacao
        payload["tipoExameSugerido"] = registro.tipo_exame
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
        payload["numeroInterno"] = registro.numero_interno
        payload["tipoExame"] = registro.tipo_exame
        payload["status"] = registro.status
        solicitacao = await self.session.get(ApSolicitacao, registro.solicitacao_id)
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

        payload["casoOrigemNumero"] = registro.caso_origem_numero
        payload["tipoDerivacao"] = registro.tipo_derivacao
        if registro.caso_origem_numero:
            origem = await self.session.get(ApCaso, registro.caso_origem_numero)
            origem_solicitacao = await self.session.get(ApSolicitacao, origem.solicitacao_id) if origem else None
            origem_payload = self._solicitacao_payload(origem_solicitacao) if origem_solicitacao else {}
            payload["casoOrigem"] = {
                "numeroInterno": origem.numero_interno,
                "tipoExame": origem.tipo_exame,
                "status": origem.status,
                "dataEntradaSap": origem.data_entrada,
                "nomePaciente": origem_payload.get("nomePaciente", ""),
                "prontuario": origem_payload.get("prontuario", ""),
            }
        else:
            payload["casoOrigem"] = None

        derivados: list[dict[str, Any]] = []
        casos_derivados_result = await self.session.execute(
            select(ApCaso)
            .where(ApCaso.caso_origem_numero == registro.numero_interno)
            .order_by(ApCaso.data_entrada.asc(), ApCaso.numero_interno.asc())
        )
        for derivado in casos_derivados_result.scalars().all():
            derivados.append({
                "codigoInterno": derivado.numero_interno,
                "numeroInterno": derivado.numero_interno,
                "tipo": derivado.tipo_derivacao or derivado.tipo_exame,
                "status": derivado.status,
                "data": derivado.data_entrada,
                "navegavel": True,
            })
        for ihq in ihqs:
            derivados.append({
                "codigoInterno": ihq["codigoInternoIhq"],
                "tipo": "IHQ",
                "status": ihq.get("status", "SOLICITADA"),
                "data": ihq.get("recebidaEm"),
                "solicitacaoAghuCodigo": ihq.get("solicitacaoAghuCodigo"),
                "navegavel": False,
            })
        payload["examesDerivados"] = sorted(derivados, key=lambda item: item.get("data") or "")

        nc_result = await self.session.execute(select(ApNaoConformidade))
        nao_conformidades: list[dict[str, Any]] = []
        for nc in nc_result.scalars().all():
            nc_payload = _load(nc.payload)
            if nc.caso_numero != registro.numero_interno and registro.numero_interno not in nc_payload.get("casoNumeros", []):
                continue
            nc_payload["id"] = nc.id
            nc_payload["status"] = nc.status
            nao_conformidades.append(nc_payload)
        payload["naoConformidades"] = nao_conformidades

        devolucoes_result = await self.session.execute(select(ApDevolucao))
        devolucoes: list[dict[str, Any]] = []
        for devolucao in devolucoes_result.scalars().all():
            devolucao_payload = _load(devolucao.payload)
            if devolucao.caso_numero != registro.numero_interno and registro.numero_interno not in devolucao_payload.get("casoNumeros", []):
                continue
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
