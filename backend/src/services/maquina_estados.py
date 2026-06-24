"""
Máquina de estados das amostras + registro de auditoria.

Toda mudança de status deve passar por `transicionar(...)`, que valida a
transição e grava um registro append-only em HISTORICO_MOVIMENTACAO (RNF010 —
rastreabilidade de 100% das transições, com usuário, timestamp e IP).

Os status do Exame seguem exatamente os valores do frontend (constants/statuses.ts).
Os status de Frasco, Cassete, Bloco e Lâmina são internos (operacionais).
"""

from fastapi import HTTPException, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.bloco_parafina import BlocoParafina
from ..models.cassete import Cassete
from ..models.exame import Exame
from ..models.frasco import Frasco
from ..models.historico_movimentacao import HistoricoMovimentacao
from ..models.lamina import Lamina
from ..models.lote_processamento import LoteProcessamento


# --- Status do Exame — devem bater exatamente com frontend/src/constants/statuses.ts ---
class StatusExame:
    NA_RECEPCAO = "Na Recepção"
    EM_MACROSCOPIA = "Em Macroscopia"
    EM_PROCESSAMENTO = "Em Processamento"
    EM_MICROSCOPIA = "Em Microscopia"
    EM_CONGELAMENTO = "Em Congelamento"
    REVISAO_PENDENTE = "Revisão Pendente"
    LIBERADO = "Liberado"


# --- Status internos/operacionais (não exibidos diretamente no dashboard) ---
class StatusFrasco:
    NA_RECEPCAO = "Na Recepção"
    AGUARDANDO_MACROSCOPIA = "Aguardando Macroscopia"
    EM_MACROSCOPIA = "Em Macroscopia"
    PROCESSAMENTO_COMPLETO = "Processamento Completo"


class StatusCassete:
    AGUARDANDO_PROCESSAMENTO = "Aguardando Processamento"
    EM_PROCESSAMENTO = "Em Processamento"
    PROCESSAMENTO_COMPLETO = "Processamento Completo"


class StatusLote:
    EM_ANDAMENTO = "Em Andamento"
    CONCLUIDO = "Concluído"


class StatusBloco:
    AGUARDANDO_CORTE = "Aguardando Corte"
    AGUARDANDO_MICROSCOPIA = "Aguardando Microscopia"


class StatusLamina:
    AGUARDANDO_LEITURA = "Aguardando Leitura"


# --- Etapas do fluxo (campo `etapa` do histórico) ---
class Etapa:
    TRIAGEM = "Triagem"
    MACROSCOPIA = "Macroscopia"
    PROCESSAMENTO = "Processamento"
    MICROSCOPIA = "Microscopia"


# --- Transições permitidas, por tipo de entidade ---
TRANSICOES_VALIDAS: dict[str, dict[str, set[str]]] = {
    "Exame": {
        StatusExame.NA_RECEPCAO: {StatusExame.EM_MACROSCOPIA},
        StatusExame.EM_MACROSCOPIA: {StatusExame.EM_PROCESSAMENTO},
        StatusExame.EM_PROCESSAMENTO: {StatusExame.EM_MICROSCOPIA},
        StatusExame.EM_MICROSCOPIA: {StatusExame.LIBERADO},
        StatusExame.EM_CONGELAMENTO: set(),
        StatusExame.REVISAO_PENDENTE: {StatusExame.LIBERADO},
        StatusExame.LIBERADO: set(),
    },
    "Frasco": {
        StatusFrasco.NA_RECEPCAO: {StatusFrasco.AGUARDANDO_MACROSCOPIA},
        StatusFrasco.AGUARDANDO_MACROSCOPIA: {StatusFrasco.EM_MACROSCOPIA},
        StatusFrasco.EM_MACROSCOPIA: {StatusFrasco.PROCESSAMENTO_COMPLETO},
        StatusFrasco.PROCESSAMENTO_COMPLETO: set(),
    },
    "Cassete": {
        StatusCassete.AGUARDANDO_PROCESSAMENTO: {StatusCassete.EM_PROCESSAMENTO},
        StatusCassete.EM_PROCESSAMENTO: {StatusCassete.PROCESSAMENTO_COMPLETO},
        StatusCassete.PROCESSAMENTO_COMPLETO: set(),
    },
    "BlocoParafina": {
        StatusBloco.AGUARDANDO_CORTE: {StatusBloco.AGUARDANDO_MICROSCOPIA},
        StatusBloco.AGUARDANDO_MICROSCOPIA: set(),
    },
}

_FK_POR_TIPO = {
    "Exame": "id_exame",
    "Frasco": "id_frasco",
    "Cassete": "id_cassete",
}


def registrar_historico(
    session: AsyncSession,
    entidade,
    *,
    status_anterior: str | None,
    status_novo: str,
    etapa: str,
    usuario: str | None = None,
    ip: str | None = None,
    observacoes: str | None = None,
) -> HistoricoMovimentacao:
    tipo = type(entidade).__name__
    fk_attr = _FK_POR_TIPO.get(tipo)
    if fk_attr is None:
        raise ValueError(f"Tipo sem mapeamento de histórico: {tipo}")

    historico = HistoricoMovimentacao(
        etapa=etapa,
        status_anterior=status_anterior,
        status_novo=status_novo,
        usuario_responsavel=usuario,
        ip_origem=ip,
        observacoes=observacoes,
        **{fk_attr: entidade.id},
    )
    session.add(historico)
    return historico


def transicionar(
    session: AsyncSession,
    entidade,
    novo_status: str,
    *,
    etapa: str,
    usuario: str | None = None,
    ip: str | None = None,
    observacoes: str | None = None,
) -> HistoricoMovimentacao:
    tipo = type(entidade).__name__
    if tipo not in TRANSICOES_VALIDAS:
        raise ValueError(f"Tipo sem máquina de estados: {tipo}")

    atual = entidade.status
    permitidos = TRANSICOES_VALIDAS[tipo].get(atual, set())
    if novo_status not in permitidos:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=(
                f"Transição inválida para {tipo}: '{atual}' -> '{novo_status}'. "
                f"Permitidas a partir de '{atual}': {sorted(permitidos) or 'nenhuma'}."
            ),
        )

    entidade.status = novo_status
    return registrar_historico(
        session,
        entidade,
        status_anterior=atual,
        status_novo=novo_status,
        etapa=etapa,
        usuario=usuario,
        ip=ip,
        observacoes=observacoes,
    )
