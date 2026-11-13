import asyncio
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.exame import (
    Amostra,
    BancadaLaboratorio,
    ConferenciaAmostra,
    Exame,
    MotivoNaoConformidade,
    NaoConformidade,
    ProcedimentoHp,
    SequenciaNumeroInterno,
    StatusItemAghu,
    STATUS_DEVOLVIDO,
    STATUS_RECEBIDO,
)
from ..interfaces.recebimento_provider_interface import RecebimentoProviderInterface

MAX_TENTATIVAS = 5
ESPERA_ENTRE_TENTATIVAS_SEGUNDOS = 0.2


def _exame_para_dict(exame: Exame, amostras: Optional[List[Amostra]] = None) -> Dict[str, Any]:
    """Converte um exame, e opcionalmente suas amostras, em dicionário."""
    dados: Dict[str, Any] = {
        "id": exame.id,
        "numero_interno": exame.numero_interno,
        "tipo": exame.tipo,
        "status": exame.status,
        "codigo_solicitacao": exame.codigo_solicitacao,
        "urgente": exame.urgente,
        "recebido_por": exame.recebido_por,
        "recebido_em": exame.recebido_em,
    }
    if amostras is not None:
        dados["amostras"] = [
            {
                "numero_amostra": amostra.numero_amostra,
                "bancada": amostra.bancada,
                "sigla_exame": amostra.sigla_exame,
                "nome_exame": amostra.nome_exame,
                "descricao_material": amostra.descricao_material,
                "descricao_informada": amostra.descricao_informada,
                "recebida": amostra.recebida,
            }
            for amostra in amostras
        ]
    return dados


class RecebimentoSqlalchemyProvider(RecebimentoProviderInterface):
    """Persistência do recebimento no banco local da aplicação, via ORM."""

    def __init__(self, session: AsyncSession) -> None:
        """Guarda a sessão do banco local."""
        self.session = session

    async def listar_bancadas(self) -> Dict[str, Dict[str, str]]:
        """Retorna bancada e prefixo dos laboratórios ativos, por `codigo_lab`."""
        resultado = await self.session.execute(
            select(BancadaLaboratorio).where(
                BancadaLaboratorio.ativo.is_(True), BancadaLaboratorio.deleted_at.is_(None)
            )
        )
        return {
            linha.codigo_lab: {"bancada": linha.bancada, "prefixo": linha.prefixo}
            for linha in resultado.scalars()
        }

    async def listar_status_item(self) -> Dict[str, Dict[str, Any]]:
        """Retorna os status de item configurados, por código."""
        resultado = await self.session.execute(
            select(StatusItemAghu).where(StatusItemAghu.deleted_at.is_(None))
        )
        return {
            linha.codigo: {
                "descricao": linha.descricao,
                "permite_recebimento": linha.permite_recebimento,
            }
            for linha in resultado.scalars()
        }

    async def listar_procedimentos_hp(self) -> List[Dict[str, Any]]:
        """Retorna os procedimentos de HP ativos."""
        resultado = await self.session.execute(
            select(ProcedimentoHp)
            .where(ProcedimentoHp.ativo.is_(True), ProcedimentoHp.deleted_at.is_(None))
            .order_by(ProcedimentoHp.id)
        )
        return [{"id": linha.id, "descricao": linha.descricao} for linha in resultado.scalars()]

    async def obter_procedimento_hp(self, procedimento_id: int) -> Optional[Dict[str, Any]]:
        """Retorna um procedimento ativo pelo id, ou None se ele não existir ou estiver inativo."""
        resultado = await self.session.execute(
            select(ProcedimentoHp).where(
                ProcedimentoHp.id == procedimento_id,
                ProcedimentoHp.ativo.is_(True),
                ProcedimentoHp.deleted_at.is_(None),
            )
        )
        linha = resultado.scalar_one_or_none()
        return {"id": linha.id, "descricao": linha.descricao} if linha else None

    async def listar_motivos(self) -> List[Dict[str, Any]]:
        """Retorna os motivos de não conformidade ativos."""
        resultado = await self.session.execute(
            select(MotivoNaoConformidade)
            .where(MotivoNaoConformidade.ativo.is_(True), MotivoNaoConformidade.deleted_at.is_(None))
            .order_by(MotivoNaoConformidade.id)
        )
        return [{"id": motivo.id, "descricao": motivo.descricao} for motivo in resultado.scalars()]

    async def obter_motivo(self, motivo_id: int) -> Optional[Dict[str, Any]]:
        """Retorna um motivo ativo pelo id, ou None se ele não existir ou estiver inativo."""
        resultado = await self.session.execute(
            select(MotivoNaoConformidade).where(
                MotivoNaoConformidade.id == motivo_id,
                MotivoNaoConformidade.ativo.is_(True),
                MotivoNaoConformidade.deleted_at.is_(None),
            )
        )
        motivo = resultado.scalar_one_or_none()
        return {"id": motivo.id, "descricao": motivo.descricao} if motivo else None

    async def listar_exames_da_solicitacao(self, codigo_solicitacao: str) -> List[Dict[str, Any]]:
        """Retorna os exames já registrados para a solicitação, do mais antigo ao mais recente."""
        resultado = await self.session.execute(
            select(Exame)
            .where(Exame.codigo_solicitacao == codigo_solicitacao, Exame.deleted_at.is_(None))
            .order_by(Exame.id)
        )
        return [_exame_para_dict(exame) for exame in resultado.scalars()]

    async def listar_historico_da_solicitacao(self, codigo_solicitacao: str) -> List[Dict[str, Any]]:
        """Retorna os exames da solicitação com tudo o que foi gravado sobre eles."""
        resultado = await self.session.execute(
            select(Exame, ProcedimentoHp.descricao)
            .outerjoin(ProcedimentoHp, Exame.procedimento_id == ProcedimentoHp.id)
            .where(Exame.codigo_solicitacao == codigo_solicitacao, Exame.deleted_at.is_(None))
            .order_by(Exame.id)
        )
        linhas_exame = resultado.all()
        ids = [exame.id for exame, _ in linhas_exame]
        if not ids:
            return []

        amostras: Dict[int, List[Dict[str, Any]]] = {}
        resultado = await self.session.execute(
            select(Amostra, ConferenciaAmostra)
            .outerjoin(ConferenciaAmostra, ConferenciaAmostra.amostra_id == Amostra.id)
            .where(Amostra.exame_id.in_(ids), Amostra.deleted_at.is_(None))
            .order_by(Amostra.numero_amostra)
        )
        for amostra, conferencia in resultado.all():
            amostras.setdefault(amostra.exame_id, []).append(
                {
                    "numero_amostra": amostra.numero_amostra,
                    "sigla_exame": amostra.sigla_exame,
                    "descricao_material": amostra.descricao_material,
                    "descricao_informada": amostra.descricao_informada,
                    "recebida": amostra.recebida,
                    "conferencia": (
                        {
                            "conferido_por": conferencia.conferido_por,
                            "conferido_em": conferencia.conferido_em,
                        }
                        if conferencia
                        else None
                    ),
                }
            )

        nao_conformidades: Dict[int, List[Dict[str, Any]]] = {}
        resultado = await self.session.execute(
            select(NaoConformidade, MotivoNaoConformidade.descricao)
            .join(MotivoNaoConformidade, NaoConformidade.motivo_id == MotivoNaoConformidade.id)
            .where(NaoConformidade.exame_id.in_(ids), NaoConformidade.deleted_at.is_(None))
            .order_by(NaoConformidade.id)
        )
        for registro, motivo in resultado.all():
            nao_conformidades.setdefault(registro.exame_id, []).append(
                {
                    "motivo": motivo,
                    "observacao": registro.observacao,
                    "numero_cmce": registro.numero_cmce,
                    "medico_solicitante": registro.medico_solicitante,
                    "resolvida": registro.resolvida,
                    "resolvida_por": registro.resolvida_por,
                    "resolvida_em": registro.resolvida_em,
                    "registrado_por": registro.registrado_por,
                    "registrado_em": registro.registrado_em,
                }
            )

        return [
            {
                **_exame_para_dict(exame),
                "quantidade_pecas": exame.quantidade_pecas,
                "procedimento": procedimento,
                "referencia_hp": exame.referencia_hp,
                "amostras": amostras.get(exame.id, []),
                "nao_conformidades": nao_conformidades.get(exame.id, []),
            }
            for exame, procedimento in linhas_exame
        ]

    async def listar_exames_das_solicitacoes(
        self, codigos_solicitacao: List[str]
    ) -> List[Dict[str, Any]]:
        """Retorna os exames já registrados de várias solicitações, para a lista da Recepção."""
        if not codigos_solicitacao:
            return []
        resultado = await self.session.execute(
            select(Exame)
            .where(Exame.codigo_solicitacao.in_(codigos_solicitacao), Exame.deleted_at.is_(None))
            .order_by(Exame.id)
        )
        return [_exame_para_dict(exame) for exame in resultado.scalars()]

    async def listar_codigos_com_exame_recebido(self, tipo: str) -> List[str]:
        """Retorna os códigos das solicitações que já têm exame RECEBIDO do tipo informado."""
        resultado = await self.session.execute(
            select(Exame.codigo_solicitacao)
            .where(
                Exame.tipo == tipo,
                Exame.status == STATUS_RECEBIDO,
                Exame.deleted_at.is_(None),
            )
            .distinct()
        )
        return list(resultado.scalars())

    async def _proximo_numero(self, tipo: str, ano: int) -> int:
        """
        Incrementa a sequência em um único comando, dentro da transação em andamento.

        A linha fica bloqueada até o commit, então duas requisições não recebem o mesmo
        número. Em um rollback, o incremento é desfeito e nenhum número é pulado.
        """
        comando = (
            sqlite_insert(SequenciaNumeroInterno)
            .values(tipo=tipo, ano=ano, ultimo_numero=1)
            .on_conflict_do_update(
                index_elements=["tipo", "ano"],
                set_={"ultimo_numero": SequenciaNumeroInterno.ultimo_numero + 1},
            )
            .returning(SequenciaNumeroInterno.ultimo_numero)
        )
        resultado = await self.session.execute(comando)
        return resultado.scalar_one()

    async def _gravar_amostras(
        self, exame: Exame, dados_amostras: List[Dict[str, Any]], usuario: str, momento: datetime
    ) -> List[Amostra]:
        """Grava as amostras do exame e a conferência das que foram recebidas."""
        amostras: List[Amostra] = []
        for dados in dados_amostras:
            amostra = Amostra(
                exame_id=exame.id,
                numero_amostra=dados["numero_amostra"],
                bancada=dados["bancada"],
                sigla_exame=dados["sigla_exame"],
                nome_exame=dados["nome_exame"],
                descricao_material=dados["descricao_material"],
                descricao_informada=dados.get("descricao_informada"),
                cod_status_item=dados["cod_status_item"],
                recebida=dados["recebida"],
            )
            self.session.add(amostra)
            await self.session.flush()
            amostras.append(amostra)

            conferencia = dados.get("conferencia")
            if conferencia:
                self.session.add(
                    ConferenciaAmostra(
                        amostra_id=amostra.id,
                        sigla_confere=conferencia["sigla_confere"],
                        descricao_confere=conferencia["descricao_confere"],
                        recipientes_confere=conferencia["recipientes_confere"],
                        conferido_por=usuario,
                        conferido_em=momento,
                    )
                )
        await self.session.flush()
        return amostras

    async def _resolver_nao_conformidades(
        self, codigo_solicitacao: str, tipo: str, usuario: str, momento: datetime
    ) -> List[int]:
        """Marca como resolvidas as não conformidades pendentes e retorna os ids."""
        resultado = await self.session.execute(
            select(NaoConformidade)
            .join(Exame, NaoConformidade.exame_id == Exame.id)
            .where(
                Exame.codigo_solicitacao == codigo_solicitacao,
                Exame.tipo == tipo,
                Exame.status == STATUS_DEVOLVIDO,
                Exame.deleted_at.is_(None),
                NaoConformidade.resolvida.is_(False),
                NaoConformidade.deleted_at.is_(None),
            )
            .order_by(NaoConformidade.id)
        )
        pendentes = list(resultado.scalars())
        for registro in pendentes:
            registro.resolvida = True
            registro.resolvida_por = usuario
            registro.resolvida_em = momento
        await self.session.flush()
        return [registro.id for registro in pendentes]

    async def _executar_em_transacao(
        self, operacao: Callable[[], Awaitable[List[Dict[str, Any]]]]
    ) -> List[Dict[str, Any]]:
        """Executa a operação em uma transação e a repete se o SQLite estiver ocupado."""
        for tentativa in range(1, MAX_TENTATIVAS + 1):
            try:
                resultado = await operacao()
                await self.session.commit()
                return resultado
            except OperationalError as erro:
                await self.session.rollback()
                if "locked" not in str(erro).lower() and "busy" not in str(erro).lower():
                    raise
                if tentativa == MAX_TENTATIVAS:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="O sistema está ocupado. Nada foi gravado; tente novamente.",
                    )
                await asyncio.sleep(ESPERA_ENTRE_TENTATIVAS_SEGUNDOS * tentativa)
            except Exception:
                await self.session.rollback()
                raise
        raise RuntimeError("Número de tentativas inválido.")

    def _novo_exame(self, dados: Dict[str, Any], situacao: str, usuario: str, momento: datetime) -> Exame:
        """Cria um exame com os dados comuns ao recebimento e à devolução."""
        return Exame(
            tipo=dados["tipo"],
            ano=dados["ano"],
            codigo_solicitacao=dados["codigo_solicitacao"],
            prontuario=dados["prontuario"],
            origem=dados["origem"],
            especialidade=dados["especialidade"],
            unidade=dados["unidade"],
            status=situacao,
            recebido_por=usuario,
            recebido_em=momento,
        )

    async def registrar_recebimento(
        self,
        exames: List[Dict[str, Any]],
        usuario: str,
        momento: datetime,
    ) -> List[Dict[str, Any]]:
        """Grava os exames recebidos e gera o nº interno de cada um em uma única transação."""

        async def operacao() -> List[Dict[str, Any]]:
            """Gera os números e grava os exames, sem confirmar a transação."""
            gravados: List[Dict[str, Any]] = []
            for dados in exames:
                sequencial = await self._proximo_numero(dados["tipo"], dados["ano"])
                exame = self._novo_exame(dados, STATUS_RECEBIDO, usuario, momento)
                exame.sequencial = sequencial
                exame.numero_interno = f"{dados['prefixo']} {sequencial}"
                exame.quantidade_pecas = dados.get("quantidade_pecas")
                exame.urgente = dados.get("urgente")
                exame.procedimento_id = dados.get("procedimento_id")
                exame.referencia_hp = dados.get("referencia_hp")
                self.session.add(exame)
                await self.session.flush()
                amostras = await self._gravar_amostras(exame, dados["amostras"], usuario, momento)
                resolvidas = await self._resolver_nao_conformidades(
                    dados["codigo_solicitacao"], dados["tipo"], usuario, momento
                )
                gravado = _exame_para_dict(exame, amostras)
                gravado["nao_conformidades_resolvidas"] = resolvidas
                gravados.append(gravado)
            return gravados

        try:
            return await self._executar_em_transacao(operacao)
        except IntegrityError:
            # Outra requisição recebeu a mesma solicitação primeiro.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=await self._detalhe_ja_recebida(exames[0]["codigo_solicitacao"]),
            )

    async def _detalhe_ja_recebida(self, codigo_solicitacao: str) -> str:
        """Monta a mensagem de recebimento duplicado com os números já existentes."""
        exames = await self.listar_exames_da_solicitacao(codigo_solicitacao)
        numeros = [exame["numero_interno"] for exame in exames if exame["status"] == STATUS_RECEBIDO]
        return f"Solicitação já recebida: {', '.join(numeros)}."

    async def registrar_nao_conformidade(
        self,
        exames: List[Dict[str, Any]],
        dados: Dict[str, Any],
        usuario: str,
        momento: datetime,
    ) -> List[Dict[str, Any]]:
        """Grava os exames como devolvidos e a não conformidade, sem consumir nº interno."""

        async def operacao() -> List[Dict[str, Any]]:
            """Grava os exames devolvidos, sem confirmar a transação."""
            gravados: List[Dict[str, Any]] = []
            for dados_exame in exames:
                exame = self._novo_exame(dados_exame, STATUS_DEVOLVIDO, usuario, momento)
                self.session.add(exame)
                await self.session.flush()
                amostras = await self._gravar_amostras(
                    exame, dados_exame["amostras"], usuario, momento
                )
                self.session.add(
                    NaoConformidade(
                        exame_id=exame.id,
                        motivo_id=dados["motivo_id"],
                        observacao=dados["observacao"],
                        numero_cmce=dados["numero_cmce"],
                        medico_solicitante=dados["medico_solicitante"],
                        resolvida=False,
                        registrado_por=usuario,
                        registrado_em=momento,
                    )
                )
                await self.session.flush()
                gravados.append(_exame_para_dict(exame, amostras))
            return gravados

        return await self._executar_em_transacao(operacao)
