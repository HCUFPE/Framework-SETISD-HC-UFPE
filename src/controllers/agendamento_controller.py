"""
Controller de Gestão de Agendamentos (v0.7.0)
============================================
Centraliza as regras de negócio: pré-condições (RN-04/RN-07), conflito de
paciente (RN-05), capacidade local, cancelamento/remarcação com justificativa,
busca segura de pacientes, sugestão automática de vagas, simulação de propostas
pendentes de confirmação, movimento de propostas por arrastar e soltar e
administração de vagas (inclusive remoção e cópia semanal) com auditoria
`CONFIGURACAO`.

A pontuação da sugestão é 0..100 com pesos configuráveis. A distância é apenas
desempate (10 pontos no máximo) e nunca supera a prioridade clínica (35 pontos).
"""

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..helpers.audit_helper import registrar_auditoria
from ..helpers.crypto_helper import to_dict_seguro
from ..helpers.string_helper import parse_datetime
from ..models.agendamento import AgendaSlot, Agendamento, ContatoPaciente, PacienteEndereco
from ..models.audit_log import AuditLog
from ..models.forms_integration import Divergencia, Solicitacao
from ..providers.interfaces.distance_provider_interface import DistanceProviderInterface
from ..providers.interfaces.slot_provider_interface import SlotProviderInterface
from ..providers.implementations.slot_provider import (
    para_iso,
    para_utc_aware,
    para_utc_naive,
)

STATUS_SLOT = {"DISPONIVEL", "LOTADO", "ENCERRADO"}
RESULTADOS_CONTATO = {"ACEITE", "RECUSA", "SEM_RESPOSTA"}
STATUS_RECEBIDA = "RECEBIDA"
STATUS_PENDENTE_CORRECAO = "PENDENTE_CORRECAO"
STATUS_AGUARDANDO_CONTATO = "AGUARDANDO_CONTATO"
STATUS_AGUARDANDO_CONFIRMACAO = "AGUARDANDO_CONFIRMACAO"
STATUS_AGUARDANDO_REAGENDAMENTO = "AGUARDANDO_REAGENDAMENTO"
STATUS_AGENDADA = "AGENDADA"
STATUS_CANCELADA = "CANCELADA"
STATUS_NAO_CONFIRMADO = "NAO_CONFIRMADO"
# Estados que permitem criar ou remarcar uma proposta/agendamento.
STATUS_AGENDAVEIS = {
    STATUS_AGUARDANDO_CONTATO,
    STATUS_AGUARDANDO_CONFIRMACAO,
    STATUS_AGUARDANDO_REAGENDAMENTO,
}
# Propostas e agendamentos ativos ocupam vaga e bloqueiam choque de paciente.
STATUS_OCUPANTES = {"ATIVO", "PROPOSTO"}
# Status que permitem cancelamento da fila de marcação.
STATUS_CANCELÁVEIS = {
    STATUS_AGUARDANDO_CONFIRMACAO,
    STATUS_NAO_CONFIRMADO,
    STATUS_AGUARDANDO_REAGENDAMENTO,
    STATUS_AGENDADA,
}


def _agora() -> datetime:
    """Retorna datetime UTC atual."""
    return datetime.now(timezone.utc)


def _erro(codigo: int, mensagem: str) -> HTTPException:
    """Padroniza erros no formato `{"detail": "..."}` do framework."""
    return HTTPException(status_code=codigo, detail=mensagem)


def _json_itens(valor: Optional[str]) -> List[Dict[str, Any]]:
    """Desserializa `itens_exame` sem falhar com dados legados."""
    if not valor:
        return []
    try:
        itens = json.loads(valor)
    except (TypeError, ValueError):
        return []
    return [item for item in itens if isinstance(item, dict)] if isinstance(itens, list) else []


async def _buscar_solicitacao(db: AsyncSession, solicitacao_id: str) -> Solicitacao:
    """Localiza uma solicitação ativa ou responde 404."""
    solicitacao = await db.scalar(
        select(Solicitacao).where(
            Solicitacao.id == solicitacao_id, Solicitacao.deleted_at.is_(None)
        )
    )
    if not solicitacao:
        raise _erro(status.HTTP_404_NOT_FOUND, "Solicitação não encontrada.")
    return solicitacao


async def _buscar_agendamento(db: AsyncSession, agendamento_id: str) -> Agendamento:
    """Localiza um agendamento ativo ou responde 404."""
    agendamento = await db.scalar(
        select(Agendamento).where(
            Agendamento.id == agendamento_id, Agendamento.deleted_at.is_(None)
        )
    )
    if not agendamento:
        raise _erro(status.HTTP_404_NOT_FOUND, "Agendamento não encontrado.")
    return agendamento


async def _divergencias_ativas(db: AsyncSession, solicitacao_id: str) -> List[Divergencia]:
    """Lista divergências ainda não tratadas (RN-04)."""
    return list(
        (
            await db.scalars(
                select(Divergencia).where(
                    Divergencia.solicitacao_id == solicitacao_id,
                    Divergencia.deleted_at.is_(None),
                    or_(Divergencia.tratada.is_(False), Divergencia.tratada.is_(None)),
                )
            )
        ).all()
    )


async def _tem_aceite(db: AsyncSession, solicitacao_id: str) -> bool:
    """Verifica se existe pelo menos um contato com resultado ACEITE (RN-07)."""
    contato = await db.scalar(
        select(ContatoPaciente.id).where(
            ContatoPaciente.solicitacao_id == solicitacao_id,
            ContatoPaciente.resultado == "ACEITE",
            ContatoPaciente.deleted_at.is_(None),
        )
    )
    return contato is not None


async def _verificar_precondicoes(
    db: AsyncSession, solicitacao: Solicitacao, *, permitir_agendada: bool = False
) -> None:
    """Aplica RN-04/RN-07 antes de criar ou remarcar um agendamento."""
    permitidos = set(STATUS_AGENDAVEIS)
    if permitir_agendada:
        permitidos.add(STATUS_AGENDADA)
    if solicitacao.status not in permitidos:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "A solicitação precisa estar aguardando contato, confirmação ou "
            "reagendamento para ser agendada.",
        )
    if await _divergencias_ativas(db, solicitacao.id):
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Existem divergências não tratadas; valide a solicitação antes de agendar.",
        )
    if not await _tem_aceite(db, solicitacao.id):
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "É necessário registrar um contato com ACEITE do paciente antes de agendar.",
        )


async def _slot_disponivel(
    provider: SlotProviderInterface, slot_id: str
) -> Dict[str, Any]:
    """Obtém a vaga e bloqueia vagas encerradas, esgotadas ou no passado."""
    slot = await provider.obter(slot_id)
    if not slot:
        raise _erro(status.HTTP_404_NOT_FOUND, "Vaga não encontrada.")
    if slot["status"] == "ENCERRADO":
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "A vaga está encerrada.")
    if para_utc_aware(parse_datetime(slot["inicio"])) < _agora():
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Não é possível agendar em uma vaga passada.",
        )
    if slot["livres"] <= 0:
        raise _erro(status.HTTP_409_CONFLICT, "Vaga esgotada para este horário.")
    return slot


async def _conflito_paciente(
    db: AsyncSession,
    paciente_chave: str,
    inicio: datetime,
    fim: datetime,
    *,
    ignorar_agendamento_id: Optional[str] = None,
) -> bool:
    """Bloqueia agendamentos ATIVOS/PROPOSTOS sobrepostos do mesmo paciente (RN-05)."""
    if not paciente_chave:
        return False
    linhas = (
        await db.execute(
            select(Agendamento.id, AgendaSlot.inicio, AgendaSlot.fim)
            .join(AgendaSlot, Agendamento.slot_id == AgendaSlot.id)
            .where(
                Agendamento.paciente_chave == paciente_chave,
                Agendamento.status.in_(STATUS_OCUPANTES),
                Agendamento.deleted_at.is_(None),
            )
        )
    ).all()
    inicio_alvo = para_utc_aware(inicio)
    fim_alvo = para_utc_aware(fim)
    for ag_id, slot_inicio, slot_fim in linhas:
        if ignorar_agendamento_id and ag_id == ignorar_agendamento_id:
            continue
        if inicio_alvo < para_utc_aware(slot_fim) and para_utc_aware(slot_inicio) < fim_alvo:
            return True
    return False


async def _agendamento_para_dict(
    db: AsyncSession,
    agendamento: Agendamento,
    provider: SlotProviderInterface,
) -> Dict[str, Any]:
    """Converte um agendamento para o DTO `Agendamento` do contrato HTTP."""
    solicitacao = await db.scalar(
        select(Solicitacao).where(Solicitacao.id == agendamento.solicitacao_id)
    )
    slot = await provider.obter(agendamento.slot_id)
    return {
        "id": agendamento.id,
        "solicitacaoId": agendamento.solicitacao_id,
        "protocolo": solicitacao.protocolo if solicitacao else "",
        "pacienteChave": agendamento.paciente_chave or (solicitacao.paciente_chave if solicitacao else ""),
        "pacienteNome": solicitacao.paciente_nome if solicitacao else "",
        "prontuario": solicitacao.prontuario if solicitacao else "",
        "unidade": slot["unidade"] if slot else (solicitacao.setor_solicitante if solicitacao else ""),
        "exame": slot["nomeExame"] if slot else (solicitacao.exame if solicitacao else ""),
        "slotId": agendamento.slot_id,
        "dataHora": slot["inicio"] if slot else para_iso(agendamento.criado_em),
        "status": agendamento.status,
        "confirmadoPor": agendamento.autor,
        "criadoEm": para_iso(agendamento.criado_em),
        "justificativa": agendamento.justificativa,
    }


def _proposta_para_fila(
    solicitacao: Solicitacao, agendamento: Dict[str, Any]
) -> Dict[str, Any]:
    """Converte uma proposta em linha da fila, sem PHI nem endereço.

    Os campos de prioridade e tempo na fila são os mesmos usados por `/fila`,
    para que a simulação seja apresentada no formato da fila de marcação.
    """
    nomes = [
        str(item.get("nomeExame") or item.get("nome_exame") or "").strip()
        for item in _json_itens(solicitacao.itens_exame)
    ]
    exames = ", ".join(nome for nome in nomes if nome) or solicitacao.exame or ""
    horas_na_fila = 0
    if solicitacao.recebida_em:
        horas_na_fila = max(
            0, int((_agora() - para_utc_aware(solicitacao.recebida_em)).total_seconds() // 3600)
        )
    return {
        "agendamentoId": agendamento["id"],
        "solicitacaoId": solicitacao.id,
        "protocolo": agendamento.get("protocolo") or solicitacao.protocolo,
        "pacienteNome": agendamento.get("pacienteNome") or solicitacao.paciente_nome,
        "prontuario": agendamento.get("prontuario") or solicitacao.prontuario,
        "prioridade": solicitacao.prioridade or "BAIXA",
        "pontuacao": int(solicitacao.pontuacao or 0),
        "unidadeSolicitante": solicitacao.setor_solicitante or "",
        "exames": exames,
        "status": agendamento.get("status") or "PROPOSTO",
        "statusSolicitacao": solicitacao.status,
        "dataHora": agendamento.get("dataHora") or "",
        "unidade": agendamento.get("unidade") or "",
        "nomeExame": agendamento.get("exame") or "",
        "recebidaEm": para_iso(solicitacao.recebida_em),
        "tempoNaFilaHoras": horas_na_fila,
    }


def _ordenar_fila_propostas(propostas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ordena propostas por prioridade, espera e protocolo."""
    return sorted(
        propostas,
        key=lambda item: (
            -int(item["pontuacao"]), item["recebidaEm"] or "", item["protocolo"] or ""
        ),
    )


async def _auditar(
    db: AsyncSession,
    *,
    usuario: str,
    categoria: str,
    acao: str,
    recurso: str,
    anteriores: Optional[Dict[str, Any]],
    novos: Optional[Dict[str, Any]],
    ip: Optional[str],
) -> None:
    """Registra auditoria com estado anterior/posterior, IP e categoria.

    `registrar_auditoria()` confirma a transação: as mutações da vaga e do
    agendamento são gravadas no mesmo commit do log de auditoria.
    """
    await registrar_auditoria(
        db=db,
        usuario=usuario or "sistema",
        categoria=categoria,
        acao=acao,
        recurso=recurso,
        dados_anteriores=to_dict_seguro(anteriores) if anteriores else None,
        dados_novos=to_dict_seguro(novos) if novos else None,
        ip_origem=ip,
    )


# ---------------------------------------------------------------------------
# Administração de vagas locais
# ---------------------------------------------------------------------------

def _validar_dados_slot(dados: Dict[str, Any], *, parcial: bool = False) -> None:
    """Valida os campos obrigatórios/coerentes de uma vaga."""
    if not parcial:
        for campo in ("unidade", "inicio", "fim", "capacidade"):
            valor = dados.get(campo)
            if valor is None or (isinstance(valor, str) and not valor.strip()):
                raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Campo '{campo}' é obrigatório.")
    if not dados:
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "Informe ao menos um campo para atualizar.")
    if "capacidade" in dados and dados["capacidade"] is not None:
        try:
            if int(dados["capacidade"]) < 1:
                raise ValueError
        except (TypeError, ValueError):
            raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "Capacidade deve ser um inteiro positivo.")
    if "situacao" in dados and dados["situacao"] is not None:
        if str(dados["situacao"]).upper() not in STATUS_SLOT:
            raise _erro(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Situação deve ser DISPONIVEL, LOTADO ou ENCERRADO.",
            )
    inicio = dados.get("inicio")
    fim = dados.get("fim")
    if inicio is not None and fim is not None and para_utc_aware(
        parse_datetime(fim)
    ) <= para_utc_aware(parse_datetime(inicio)):
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "O fim da vaga deve ser posterior ao início.")


async def criar_slot(
    db: AsyncSession,
    provider: SlotProviderInterface,
    *,
    dados: Dict[str, Any],
    autor: str,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Cria uma vaga local e registra auditoria CONFIGURACAO."""
    _validar_dados_slot(dados)
    slot = await provider.criar(dados)
    await _auditar(
        db,
        usuario=autor,
        categoria="CONFIGURACAO",
        acao="CRIAR_SLOT_AGENDA",
        recurso=f"agenda-slot:{slot['id']}",
        anteriores=None,
        novos=slot,
        ip=ip,
    )
    return slot


async def atualizar_slot(
    db: AsyncSession,
    provider: SlotProviderInterface,
    *,
    slot_id: str,
    dados: Dict[str, Any],
    autor: str,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Atualiza uma vaga local e registra auditoria CONFIGURACAO."""
    _validar_dados_slot(dados, parcial=True)
    anterior = await provider.obter(slot_id)
    if not anterior:
        raise _erro(status.HTTP_404_NOT_FOUND, "Vaga não encontrada.")
    if dados.get("capacidade") is not None and int(dados["capacidade"]) < int(
        anterior.get("ocupadas") or 0
    ):
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "A capacidade não pode ficar abaixo das vagas já ocupadas.",
        )
    atualizado = await provider.atualizar(slot_id, dados)
    if not atualizado:
        raise _erro(status.HTTP_404_NOT_FOUND, "Vaga não encontrada.")
    await _auditar(
        db,
        usuario=autor,
        categoria="CONFIGURACAO",
        acao="ATUALIZAR_SLOT_AGENDA",
        recurso=f"agenda-slot:{slot_id}",
        anteriores=anterior,
        novos=atualizado,
        ip=ip,
    )
    return atualizado


async def remover_slot(
    db: AsyncSession,
    provider: SlotProviderInterface,
    *,
    slot_id: str,
    autor: str,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Remove uma vaga vazia por soft delete e registra auditoria CONFIGURACAO."""
    anterior = await provider.obter(slot_id)
    if not anterior:
        raise _erro(status.HTTP_404_NOT_FOUND, "Vaga não encontrada.")
    if int(anterior.get("ocupadas") or 0) > 0:
        raise _erro(
            status.HTTP_409_CONFLICT,
            "Não é possível remover uma vaga com agendamentos ativos ou propostas.",
        )
    removido = await provider.remover(slot_id)
    if not removido:
        raise _erro(status.HTTP_404_NOT_FOUND, "Vaga não encontrada.")
    await _auditar(
        db,
        usuario=autor,
        categoria="CONFIGURACAO",
        acao="REMOVER_SLOT_AGENDA",
        recurso=f"agenda-slot:{slot_id}",
        anteriores=anterior,
        novos=None,
        ip=ip,
    )
    return removido


def _inicio_semana(valor: Any, campo: str) -> datetime:
    """Interpreta uma data/ISO e devolve a segunda-feira da semana em UTC."""
    try:
        data = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Campo '{campo}' deve ser uma data ISO.")
    if data.tzinfo is None:
        data = data.replace(tzinfo=timezone.utc)
    inicio = data - timedelta(days=data.weekday())
    return inicio.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)


def _chave_vaga(slot: Dict[str, Any]) -> tuple[str, str, datetime]:
    """Chave de identificação de uma vaga para evitar duplicatas na cópia."""
    return (
        str(slot.get("unidade") or ""),
        str(slot.get("codigoExame") or ""),
        para_utc_aware(parse_datetime(slot.get("inicio"))),
    )


async def copiar_semana(
    db: AsyncSession,
    provider: SlotProviderInterface,
    *,
    origem: str,
    destino: str,
    codigo_exame: Optional[str],
    autor: str,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Copia vagas de uma semana para outra preservando dia, horário e capacidade.

    A operação é idempotente: vagas já existentes na semana de destino (mesma
    unidade, exame e horário) são ignoradas. Toda a operação é auditada como
    `CONFIGURACAO` em um único registro, com as vagas criadas no estado novo.
    """
    inicio = _inicio_semana(origem, "origem")
    alvo = _inicio_semana(destino, "destino")
    if inicio == alvo:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "A semana de destino deve ser diferente da semana de origem.",
        )

    deslocamento = alvo - inicio
    fim_consulta = max(inicio, alvo) + timedelta(days=7)
    existentes = await provider.listar(de=inicio, ate=fim_consulta)
    filtro_exame = str(codigo_exame or "").strip()
    candidatas = [
        slot for slot in existentes
        if _inicio_semana(slot.get("inicio"), "inicio") == inicio
        and (not filtro_exame or str(slot.get("codigoExame") or "") == filtro_exame)
    ]
    if not candidatas:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Não há vagas para copiar na semana de origem.",
        )

    chaves = {_chave_vaga(slot) for slot in existentes}
    criadas: List[Dict[str, Any]] = []
    ignoradas: List[Dict[str, str]] = []
    for slot in candidatas:
        novo_inicio = para_iso(parse_datetime(slot["inicio"]) + deslocamento)
        novo_fim = para_iso(parse_datetime(slot["fim"]) + deslocamento)
        copia = {
            "unidade": slot["unidade"],
            "codigoExame": slot.get("codigoExame") or "",
            "nomeExame": slot.get("nomeExame") or "",
            "inicio": novo_inicio,
            "fim": novo_fim,
            "capacidade": slot["capacidade"],
            "situacao": slot.get("status") or "DISPONIVEL",
        }
        chave = _chave_vaga(copia)
        if chave in chaves:
            ignoradas.append({"id": str(slot["id"]), "inicio": novo_inicio or ""})
            continue
        criada = await provider.criar(copia)
        chaves.add(chave)
        criadas.append(criada)

    await _auditar(
        db,
        usuario=autor,
        categoria="CONFIGURACAO",
        acao="COPIAR_SEMANA_SLOT_AGENDA",
        recurso=f"agenda-slot-semana:{alvo.date().isoformat()}",
        anteriores={
            "origem": inicio.date().isoformat(),
            "destino": alvo.date().isoformat(),
            "codigoExame": filtro_exame,
            "candidatas": len(candidatas),
        },
        novos={
            "origem": inicio.date().isoformat(),
            "destino": alvo.date().isoformat(),
            "criadas": [str(slot["id"]) for slot in criadas],
            "ignoradas": ignoradas,
        },
        ip=ip,
    )
    return {
        "origem": inicio.date().isoformat(),
        "destino": alvo.date().isoformat(),
        "codigoExame": filtro_exame,
        "criadas": criadas,
        "ignoradas": len(ignoradas),
        "total": len(candidatas),
    }


# ---------------------------------------------------------------------------
# Solicitações: validação e contato do paciente
# ---------------------------------------------------------------------------

async def validar_divergencias(
    db: AsyncSession,
    *,
    solicitacao_id: str,
    justificativas: Optional[Dict[str, str]],
    autor: str,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Trata divergências ativas e movesolicitação para AGUARDANDO_CONTATO."""
    solicitacao = await _buscar_solicitacao(db, solicitacao_id)
    divergencias = await _divergencias_ativas(db, solicitacao_id)
    mapa = justificativas or {}
    antes = {
        "status": solicitacao.status,
        "divergenciasAtivas": len(divergencias),
    }
    for divergencia in divergencias:
        divergencia.tratada = True
        divergencia.justificativa = str(
            mapa.get(str(divergencia.id))
            or mapa.get(divergencia.campo)
            or "Divergência validada pelo operador"
        )
    solicitacao.status = STATUS_AGUARDANDO_CONTATO
    solicitacao.atualizado_em = _agora()
    await db.flush()
    await _auditar(
        db,
        usuario=autor,
        categoria="NEGOCIO_CLINICO",
        acao="VALIDAR_DIVERGENCIAS",
        recurso=f"solicitacao:{solicitacao_id}",
        anteriores=antes,
        novos={
            "status": solicitacao.status,
            "divergenciasTratadas": len(divergencias),
            "justificativasInformadas": sorted(str(chave) for chave in mapa),
        },
        ip=ip,
    )
    return {
        "solicitacaoId": solicitacao_id,
        "status": solicitacao.status,
        "divergenciasTratadas": len(divergencias),
    }


async def registrar_contato(
    db: AsyncSession,
    *,
    solicitacao_id: str,
    canal: str,
    resultado: str,
    observacao: Optional[str],
    operador: str,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Registra aceite/recusa/sem resposta e atualiza o estado da solicitação."""
    solicitacao = await _buscar_solicitacao(db, solicitacao_id)
    if solicitacao.status not in {
        STATUS_AGUARDANDO_CONTATO,
        STATUS_AGUARDANDO_CONFIRMACAO,
        STATUS_AGUARDANDO_REAGENDAMENTO,
    }:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Contatos só podem ser registrados enquanto a solicitação aguarda "
            "contato, confirmação ou reagendamento.",
        )
    if resultado not in RESULTADOS_CONTATO:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Resultado deve ser ACEITE, RECUSA ou SEM_RESPOSTA.",
        )
    status_anterior = solicitacao.status
    contato = ContatoPaciente(
        id=str(uuid.uuid4()),
        solicitacao_id=solicitacao_id,
        canal=canal,
        resultado=resultado,
        observacao=observacao,
        operador=operador,
        realizado_em=_agora(),
    )
    solicitacao.status = (
        STATUS_AGUARDANDO_CONFIRMACAO
        if resultado == "ACEITE"
        else STATUS_AGUARDANDO_REAGENDAMENTO
    )
    solicitacao.atualizado_em = _agora()
    db.add(contato)
    await db.flush()
    resposta = {
        "id": contato.id,
        "solicitacaoId": solicitacao_id,
        "canal": contato.canal,
        "resultado": contato.resultado,
        "observacao": contato.observacao,
        "operador": contato.operador,
        "realizadoEm": para_iso(contato.realizado_em),
    }
    # A observação pode conter dados informados pelo paciente: não entra na auditoria.
    await _auditar(
        db,
        usuario=operador,
        categoria="NEGOCIO_CLINICO",
        acao="REGISTRAR_CONTATO_PACIENTE",
        recurso=f"solicitacao:{solicitacao_id}",
        anteriores={"status": status_anterior},
        novos={
            "status": solicitacao.status,
            "contatoId": contato.id,
            "canal": contato.canal,
            "resultado": contato.resultado,
            "operador": contato.operador,
        },
        ip=ip,
    )
    return resposta


# ---------------------------------------------------------------------------
# Verificação automática de não confirmação (24h)
# ---------------------------------------------------------------------------

async def verificar_e_atualizar_nao_confirmados(
    db: AsyncSession,
    ip: Optional[str],
) -> List[Dict[str, Any]]:
    """Move solicitações em AGUARDANDO_CONFIRMACAO há mais de 24h para NAO_CONFIRMADO.

    A verificação usa a tabela de auditoria para encontrar quando o status
    mudou para AGUARDANDO_CONFIRMACAO. Para cada solicitação expirada, o
    status passa para NAO_CONFIRMADO e o agendamento associado é cancelado,
    liberando a vaga.
    """
    agora = _agora()
    limite = agora - timedelta(hours=24)

    # Busca solicitações em AGUARDANDO_CONFIRMACAO.
    resultado = await db.execute(
        select(Solicitacao).where(
            Solicitacao.status == STATUS_AGUARDANDO_CONFIRMACAO,
            Solicitacao.deleted_at.is_(None),
        )
    )
    solicitacoes = resultado.scalars().all()

    atualizadas: List[Dict[str, Any]] = []
    for solicitacao in solicitacoes:
        # Verifica a última mudança de status para AGUARDANDO_CONFIRMACAO na auditoria.
        ultimo = await db.execute(
            select(AuditLog)
            .where(
                AuditLog.recurso == f"solicitacao:{solicitacao.id}",
                AuditLog.categoria == "NEGOCIO_CLINICO",
                AuditLog.dados_novos.like(f'%"status": "{STATUS_AGUARDANDO_CONFIRMACAO}"%'),
            )
            .order_by(AuditLog.created_at.desc())
            .limit(1)
        )
        entrada = ultimo.scalars().first()
        if not entrada:
            continue
        mudanca_em = entrada.created_at
        if mudanca_em.tzinfo is None:
            mudanca_em = mudanca_em.replace(tzinfo=timezone.utc)
        if mudanca_em >= limite:
            continue

        # Atualiza para NAO_CONFIRMADO.
        status_anterior = solicitacao.status
        solicitacao.status = STATUS_NAO_CONFIRMADO
        solicitacao.atualizado_em = _agora()
        await db.flush()

        # Cancela o agendamento associado (libera a vaga).
        agendamento = await db.execute(
            select(Agendamento).where(
                Agendamento.solicitacao_id == solicitacao.id,
                Agendamento.status.in_(STATUS_OCUPANTES),
                Agendamento.deleted_at.is_(None),
            )
        )
        ag = agendamento.scalars().first()
        if ag:
            ag_status_anterior = ag.status
            ag.status = "CANCELADO"
            ag.justificativa = "Não confirmado pelo paciente após 24h."
            ag.cancelado_em = _agora()
            await db.flush()

        await _auditar(
            db,
            usuario="Sistema",
            categoria="NEGOCIO_CLINICO",
            acao="MARCAR_NAO_CONFIRMADO",
            recurso=f"solicitacao:{solicitacao.id}",
            anteriores={"statusSolicitacao": status_anterior},
            novos={"statusSolicitacao": STATUS_NAO_CONFIRMADO},
            ip=ip,
        )
        atualizadas.append({
            "solicitacaoId": solicitacao.id,
            "protocolo": solicitacao.protocolo,
            "statusAnterior": status_anterior,
            "statusNovo": STATUS_NAO_CONFIRMADO,
        })

    return atualizadas


# ---------------------------------------------------------------------------
# Operações da fila de marcação
# ---------------------------------------------------------------------------

async def agendar_da_fila(
    db: AsyncSession,
    provider: SlotProviderInterface,
    *,
    solicitacao_id: str,
    slot_id: str,
    autor: str,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Efetiva o agendamento a partir da fila.

    A solicitação deve estar em RECEBIDA. Cria um agendamento ATIVO no slot
    informado e move a solicitação para AGUARDANDO_CONTATO.

    A vaga é marcada antes do contato com o paciente (RN-07), por isso este
    fluxo não exige aceite prévio; o contato e a confirmação vêm depois. As
    divergências pendentes continuam bloqueando o agendamento (RN-04).
    """
    solicitacao = await _buscar_solicitacao(db, solicitacao_id)
    if solicitacao.status != STATUS_RECEBIDA:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Somente solicitações recebidas podem ser agendadas da fila.",
        )
    if await _divergencias_ativas(db, solicitacao.id):
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Existem divergências não tratadas; valide a solicitação antes de agendar.",
        )
    slot = await _slot_disponivel(provider, slot_id)

    chave = solicitacao.paciente_chave or ""
    if await _conflito_paciente(
        db, chave, parse_datetime(slot["inicio"]), parse_datetime(slot["fim"])
    ):
        raise _erro(
            status.HTTP_409_CONFLICT,
            "Já existe agendamento ativo para este paciente neste intervalo.",
        )

    agendamento = Agendamento(
        id=str(uuid.uuid4()),
        solicitacao_id=solicitacao_id,
        slot_id=slot_id,
        paciente_chave=chave,
        status="ATIVO",
        autor=autor,
        criado_em=_agora(),
    )
    status_anterior = solicitacao.status
    solicitacao.status = STATUS_AGUARDANDO_CONTATO
    solicitacao.atualizado_em = _agora()
    db.add(agendamento)
    await db.flush()
    dto = await _agendamento_para_dict(db, agendamento, provider)
    await _auditar(
        db,
        usuario=autor,
        categoria="NEGOCIO_CLINICO",
        acao="AGENDAR_DA_FILA",
        recurso=f"solicitacao:{solicitacao_id}",
        anteriores={"statusSolicitacao": status_anterior},
        novos={**dto, "statusSolicitacao": solicitacao.status},
        ip=ip,
    )
    return dto


async def cancelar_da_fila(
    db: AsyncSession,
    provider: SlotProviderInterface,
    *,
    solicitacao_id: str,
    justificativa: str,
    autor: str,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Cancela o agendamento e devolve a solicitação para RECEBIDA."""
    if not justificativa or not justificativa.strip():
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Justificativa é obrigatória para cancelar.",
        )
    solicitacao = await _buscar_solicitacao(db, solicitacao_id)
    if solicitacao.status not in STATUS_CANCELÁVEIS:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Somente solicitações em confirmação, não confirmadas, aguardando "
            "reagendamento ou agendadas podem ser canceladas.",
        )

    status_anterior = solicitacao.status
    solicitacao.status = STATUS_RECEBIDA
    solicitacao.atualizado_em = _agora()

    # Cancela o agendamento associado (libera a vaga).
    agendamento = await db.execute(
        select(Agendamento).where(
            Agendamento.solicitacao_id == solicitacao_id,
            Agendamento.status.in_(STATUS_OCUPANTES),
            Agendamento.deleted_at.is_(None),
        )
    )
    ag = agendamento.scalars().first()
    ag_dto = None
    if ag:
        ag_anterior = ag.status
        ag.status = "CANCELADO"
        ag.justificativa = justificativa.strip()
        ag.cancelado_em = _agora()
        ag.autor = autor
        await db.flush()
        ag_dto = await _agendamento_para_dict(db, ag, provider)

    await _auditar(
        db,
        usuario=autor,
        categoria="NEGOCIO_CLINICO",
        acao="CANCELAR_DA_FILA",
        recurso=f"solicitacao:{solicitacao_id}",
        anteriores={"statusSolicitacao": status_anterior},
        novos={
            "statusSolicitacao": solicitacao.status,
            "motivo": justificativa.strip(),
            "agendamentoCancelado": ag_dto is not None,
        },
        ip=ip,
    )
    return {
        "solicitacaoId": solicitacao_id,
        "status": solicitacao.status,
        "agendamentoCancelado": ag_dto is not None,
    }


async def reagendar_da_fila(
    db: AsyncSession,
    provider: SlotProviderInterface,
    *,
    solicitacao_id: str,
    slot_id: str,
    justificativa: str,
    autor: str,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Reagenda a solicitação mantendo o status AGENDADA."""
    if not justificativa or not justificativa.strip():
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Justificativa é obrigatória para reagendar.",
        )
    solicitacao = await _buscar_solicitacao(db, solicitacao_id)
    if solicitacao.status != STATUS_AGENDADA:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Somente solicitações agendadas podem ser reagendadas.",
        )
    slot = await _slot_disponivel(provider, slot_id)

    chave = solicitacao.paciente_chave or ""
    if await _conflito_paciente(
        db, chave, parse_datetime(slot["inicio"]), parse_datetime(slot["fim"])
    ):
        raise _erro(
            status.HTTP_409_CONFLICT,
            "Já existe agendamento ativo para este paciente neste intervalo.",
        )

    # Busca o agendamento atual para auditoria.
    agendamento_atual = await db.execute(
        select(Agendamento).where(
            Agendamento.solicitacao_id == solicitacao_id,
            Agendamento.status == "ATIVO",
            Agendamento.deleted_at.is_(None),
        )
    )
    ag_atual = agendamento_atual.scalars().first()
    if not ag_atual:
        raise _erro(
            status.HTTP_404_NOT_FOUND,
            "Nenhum agendamento ativo encontrado para esta solicitação.",
        )

    slot_anterior_id = ag_atual.slot_id
    ag_atual.slot_id = slot_id
    ag_atual.justificativa = justificativa.strip()
    ag_atual.autor = autor
    await db.flush()
    dto = await _agendamento_para_dict(db, ag_atual, provider)

    await _auditar(
        db,
        usuario=autor,
        categoria="NEGOCIO_CLINICO",
        acao="REAGENDAR_DA_FILA",
        recurso=f"solicitacao:{solicitacao_id}",
        anteriores={
            "statusSolicitacao": solicitacao.status,
            "slotAnterior": slot_anterior_id,
        },
        novos={
            "statusSolicitacao": solicitacao.status,
            "slotNovo": slot_id,
            "motivo": justificativa.strip(),
        },
        ip=ip,
    )
    return dto


# ---------------------------------------------------------------------------
# Agendamentos
# ---------------------------------------------------------------------------

async def criar_agendamento(
    db: AsyncSession,
    provider: SlotProviderInterface,
    *,
    solicitacao_id: str,
    slot_id: str,
    autor: str,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Efetiva um agendamento após validações RN-04/RN-05/RN-07."""
    solicitacao = await _buscar_solicitacao(db, solicitacao_id)
    await _verificar_precondicoes(db, solicitacao)
    slot = await _slot_disponivel(provider, slot_id)

    ja_agendada = await db.scalar(
        select(Agendamento.id).where(
            Agendamento.solicitacao_id == solicitacao_id,
            Agendamento.status.in_(STATUS_OCUPANTES),
            Agendamento.deleted_at.is_(None),
        )
    )
    if ja_agendada:
        raise _erro(
            status.HTTP_409_CONFLICT,
            "Esta solicitação já possui agendamento ativo ou proposta pendente.",
        )

    chave = solicitacao.paciente_chave or ""
    if await _conflito_paciente(
        db, chave, parse_datetime(slot["inicio"]), parse_datetime(slot["fim"])
    ):
        raise _erro(
            status.HTTP_409_CONFLICT,
            "Já existe agendamento ativo para este paciente neste intervalo.",
        )

    agendamento = Agendamento(
        id=str(uuid.uuid4()),
        solicitacao_id=solicitacao_id,
        slot_id=slot_id,
        paciente_chave=chave,
        status="ATIVO",
        autor=autor,
        criado_em=_agora(),
    )
    status_anterior = solicitacao.status
    solicitacao.status = STATUS_AGENDADA
    solicitacao.atualizado_em = _agora()
    db.add(agendamento)
    await db.flush()
    dto = await _agendamento_para_dict(db, agendamento, provider)
    await _auditar(
        db,
        usuario=autor,
        categoria="NEGOCIO_CLINICO",
        acao="CRIAR_AGENDAMENTO",
        recurso=f"agendamento:{agendamento.id}",
        anteriores={"statusSolicitacao": status_anterior},
        novos={**dto, "statusSolicitacao": solicitacao.status},
        ip=ip,
    )
    return dto


async def remarcar_agendamento(
    db: AsyncSession,
    provider: SlotProviderInterface,
    *,
    agendamento_id: str,
    slot_id: str,
    justificativa: Optional[str],
    autor: str,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Troca a vaga, devolvendo a antiga na mesma transação do log."""
    if not justificativa or not justificativa.strip():
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Justificativa é obrigatória para remarcar um agendamento.",
        )
    agendamento = await _buscar_agendamento(db, agendamento_id)
    if agendamento.status not in STATUS_OCUPANTES:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Somente agendamentos ativos ou propostos podem ser remarcados.",
        )
    if slot_id == agendamento.slot_id:
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "A vaga informada já é a atual.")
    solicitacao = await _buscar_solicitacao(db, agendamento.solicitacao_id)
    await _verificar_precondicoes(db, solicitacao, permitir_agendada=True)
    slot = await _slot_disponivel(provider, slot_id)
    if await _conflito_paciente(
        db,
        agendamento.paciente_chave,
        parse_datetime(slot["inicio"]),
        parse_datetime(slot["fim"]),
        ignorar_agendamento_id=agendamento_id,
    ):
        raise _erro(
            status.HTTP_409_CONFLICT,
            "Já existe agendamento ativo para este paciente neste intervalo.",
        )

    anterior = await _agendamento_para_dict(db, agendamento, provider)
    agendamento.slot_id = slot_id
    agendamento.justificativa = justificativa.strip()
    await db.flush()
    atualizado = await _agendamento_para_dict(db, agendamento, provider)
    await _auditar(
        db,
        usuario=autor,
        categoria="NEGOCIO_CLINICO",
        acao="REMARCAR_AGENDAMENTO",
        recurso=f"agendamento:{agendamento_id}",
        anteriores=anterior,
        novos={**atualizado, "motivo": justificativa.strip()},
        ip=ip,
    )
    return atualizado


async def cancelar_agendamento(
    db: AsyncSession,
    provider: SlotProviderInterface,
    *,
    agendamento_id: str,
    justificativa: Optional[str],
    autor: str,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Cancela o agendamento e devolve a vaga na mesma transação do log."""
    if not justificativa or not justificativa.strip():
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Justificativa é obrigatória para cancelar um agendamento.",
        )
    agendamento = await _buscar_agendamento(db, agendamento_id)
    if agendamento.status not in STATUS_OCUPANTES:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Somente agendamentos ativos ou propostos podem ser cancelados.",
        )
    anterior = await _agendamento_para_dict(db, agendamento, provider)
    era_proposta = agendamento.status == "PROPOSTO"
    agendamento.status = "CANCELADO"
    agendamento.justificativa = justificativa.strip()
    agendamento.cancelado_em = _agora()
    solicitacao = await _buscar_solicitacao(db, agendamento.solicitacao_id)
    status_anterior_solicitacao = solicitacao.status
    solicitacao.status = (
        STATUS_AGUARDANDO_REAGENDAMENTO if era_proposta else STATUS_CANCELADA
    )
    solicitacao.atualizado_em = _agora()
    await db.flush()
    atualizado = await _agendamento_para_dict(db, agendamento, provider)
    await _auditar(
        db,
        usuario=autor,
        categoria="NEGOCIO_CLINICO",
        acao="CANCELAR_AGENDAMENTO",
        recurso=f"agendamento:{agendamento_id}",
        anteriores=anterior,
        novos={
            **atualizado,
            "motivo": justificativa.strip(),
            "statusSolicitacao": solicitacao.status,
            "statusSolicitacaoAnterior": status_anterior_solicitacao,
        },
        ip=ip,
    )
    return atualizado


# ---------------------------------------------------------------------------
# Simulação da agenda: propostas pendentes de confirmação
# ---------------------------------------------------------------------------

async def gerar_propostas(
    db: AsyncSession,
    provider: SlotProviderInterface,
    *,
    dias: int,
    autor: str,
    unidade: Optional[str] = None,
    codigo_exame: Optional[str] = None,
    paciente_chave: Optional[str] = None,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Pré-aloca solicitações elegíveis em vagas dos próximos `dias` dias.

    A proposta reserva vaga (status PROPOSTO), mas só se torna agendamento
    ATIVO após confirmação explícita do operador. Nenhuma confirmação de
    paciente é presumida além do ACEITE já registrado no contato.
    Uma solicitação com múltiplos exames pode gerar uma proposta por exame,
    cada qual em vaga e dia distintos conforme disponibilidade. Solicitações
    ou exames que não encontram vaga são contabilizados em `deFora`.
    A simulação respeita os filtros ativos (unidade, código de exame e
    paciente/prontuário); nunca simula todas as solicitações de uma vez.
    """
    horizonte_dias = max(1, min(int(dias), 90))
    agora = _agora()
    limite = agora + timedelta(days=horizonte_dias)
    slots = await provider.listar(de=agora, ate=limite)
    elegiveis = (
        await db.scalars(
            select(Solicitacao)
            .where(
                Solicitacao.deleted_at.is_(None),
                Solicitacao.status.in_(STATUS_AGENDAVEIS),
            )
            .order_by(Solicitacao.pontuacao.desc(), Solicitacao.recebida_em)
        )
    ).all()

    # Aplica os filtros ativos sobre as solicitações elegíveis.
    unidade_filtro = (unidade or "").strip().lower()
    codigo_exame_filtro = (codigo_exame or "").strip().upper()
    paciente_chave_filtro = (paciente_chave or "").strip()

    elegiveis_filtradas = []
    for solicitacao in elegiveis:
        if unidade_filtro and (solicitacao.setor_solicitante or "").strip().lower() != unidade_filtro:
            continue
        if paciente_chave_filtro and (solicitacao.paciente_chave or "") != paciente_chave_filtro:
            continue
        if codigo_exame_filtro:
            codigos = {
                str(item.get("codigoExame") or "").strip().upper()
                for item in _json_itens(solicitacao.itens_exame)
                if item.get("codigoExame")
            }
            if codigo_exame_filtro not in codigos:
                continue
        elegiveis_filtradas.append(solicitacao)

    ja_reservadas = (
        await db.scalars(
            select(Agendamento.solicitacao_id).where(
                Agendamento.status.in_(STATUS_OCUPANTES),
                Agendamento.deleted_at.is_(None),
            )
        )
    ).all()
    reservadas = set(ja_reservadas)

    geradas: List[Dict[str, Any]] = []
    linhas_fila: List[Dict[str, Any]] = []
    usadas_por_dia: dict[str, set[str]] = {}
    alocadas_por_slot: dict[str, int] = {}
    de_fora = 0
    for solicitacao in elegiveis_filtradas:
        if solicitacao.id in reservadas:
            continue
        if not await _tem_aceite(db, solicitacao.id):
            continue
        if await _divergencias_ativas(db, solicitacao.id):
            continue
        codigos = {
            str(item.get("codigoExame") or "").strip().upper()
            for item in _json_itens(solicitacao.itens_exame)
            if item.get("codigoExame")
        }
        chave = solicitacao.paciente_chave or ""
        exames_para_tentar = list(codigos) if codigos else [None]
        for codigo in exames_para_tentar:
            elegiveis_slots = [
                slot for slot in slots
                if slot["status"] == "DISPONIVEL"
                and slot["livres"] - alocadas_por_slot.get(slot["id"], 0) > 0
                and para_utc_aware(parse_datetime(slot["inicio"])) >= agora
                and para_utc_aware(parse_datetime(slot["inicio"])) <= limite
                and (codigo is None
                     or str(slot["codigoExame"] or "").strip().upper() == codigo)
                and chave not in usadas_por_dia.get(slot["inicio"][:10], set())
            ]
            elegiveis_slots.sort(
                key=lambda item: (
                    para_utc_aware(parse_datetime(item["inicio"])),
                    -((item["livres"] - alocadas_por_slot.get(item["id"], 0))
                      / max(1, item["capacidade"])),
                )
            )
            if not elegiveis_slots:
                de_fora += 1
                continue
            slot = elegiveis_slots[0]
            if await _conflito_paciente(
                db, chave, parse_datetime(slot["inicio"]), parse_datetime(slot["fim"])
            ):
                de_fora += 1
                continue
            proposta = Agendamento(
                id=str(uuid.uuid4()),
                solicitacao_id=solicitacao.id,
                slot_id=slot["id"],
                paciente_chave=chave,
                status="PROPOSTO",
                autor=autor,
                criado_em=_agora(),
            )
            status_anterior = solicitacao.status
            solicitacao.status = STATUS_AGUARDANDO_CONFIRMACAO
            solicitacao.atualizado_em = _agora()
            db.add(proposta)
            await db.flush()
            usadas_por_dia.setdefault(slot["inicio"][:10], set()).add(chave)
            alocadas_por_slot[slot["id"]] = alocadas_por_slot.get(slot["id"], 0) + 1
            reservadas.add(solicitacao.id)
            dto = await _agendamento_para_dict(db, proposta, provider)
            geradas.append({**dto, "statusSolicitacaoAnterior": status_anterior})
            linhas_fila.append(_proposta_para_fila(solicitacao, dto))
            await _auditar(
                db,
                usuario=autor,
                categoria="NEGOCIO_CLINICO",
                acao="GERAR_PROPOSTA_AGENDA",
                recurso=f"agendamento:{proposta.id}",
                anteriores={"statusSolicitacao": status_anterior},
                novos={**dto, "statusSolicitacao": STATUS_AGUARDANDO_CONFIRMACAO},
                ip=ip,
            )
    return {
        "geradas": len(geradas),
        "solicitacoes": len(elegiveis_filtradas),
        "dias": horizonte_dias,
        "deFora": de_fora,
        "propostas": _ordenar_fila_propostas(linhas_fila),
    }


async def listar_propostas(
    db: AsyncSession, provider: SlotProviderInterface
) -> List[Dict[str, Any]]:
    """Lista as propostas pendentes no formato da fila, por prioridade."""
    linhas = (
        await db.execute(
            select(Agendamento, Solicitacao)
            .join(Solicitacao, Agendamento.solicitacao_id == Solicitacao.id)
            .where(
                Agendamento.status == "PROPOSTO",
                Agendamento.deleted_at.is_(None),
                Solicitacao.deleted_at.is_(None),
            )
        )
    ).all()
    propostas = [
        _proposta_para_fila(solicitacao, await _agendamento_para_dict(db, agendamento, provider))
        for agendamento, solicitacao in linhas
    ]
    return _ordenar_fila_propostas(propostas)


async def confirmar_proposta(
    db: AsyncSession,
    provider: SlotProviderInterface,
    *,
    agendamento_id: str,
    autor: str,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Confirma a proposta em um clique, sem nova confirmação do paciente."""
    agendamento = await _buscar_agendamento(db, agendamento_id)
    if agendamento.status != "PROPOSTO":
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Somente propostas pendentes podem ser confirmadas.",
        )
    anterior = await _agendamento_para_dict(db, agendamento, provider)
    solicitacao = await _buscar_solicitacao(db, agendamento.solicitacao_id)
    status_anterior = solicitacao.status
    agendamento.status = "ATIVO"
    agendamento.autor = autor
    solicitacao.status = STATUS_AGENDADA
    solicitacao.atualizado_em = _agora()
    await db.flush()
    atualizado = await _agendamento_para_dict(db, agendamento, provider)
    await _auditar(
        db,
        usuario=autor,
        categoria="NEGOCIO_CLINICO",
        acao="CONFIRMAR_PROPOSTA_AGENDA",
        recurso=f"agendamento:{agendamento_id}",
        anteriores={**anterior, "statusSolicitacao": status_anterior},
        novos={**atualizado, "statusSolicitacao": STATUS_AGENDADA},
        ip=ip,
    )
    return atualizado


async def mover_proposta(
    db: AsyncSession,
    provider: SlotProviderInterface,
    *,
    agendamento_id: str,
    slot_id: str,
    autor: str,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Move uma proposta para outra vaga sem confirmá-la (arrastar e soltar).

    Somente propostas `PROPOSTO` podem ser movidas. A vaga de destino precisa
    existir, estar disponível e ser compatível com o exame solicitado; além
    disso, não pode sobrepor outro agendamento/proposta do mesmo paciente.
    O status da solicitação permanece aguardando confirmação e o movimento é
    auditado como `NEGOCIO_CLINICO`.
    """
    agendamento = await _buscar_agendamento(db, agendamento_id)
    if agendamento.status != "PROPOSTO":
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Somente propostas pendentes podem ser movidas.",
        )
    if slot_id == agendamento.slot_id:
        raise _erro(status.HTTP_422_UNPROCESSABLE_ENTITY, "A vaga informada já é a atual.")

    solicitacao = await _buscar_solicitacao(db, agendamento.solicitacao_id)
    await _verificar_precondicoes(db, solicitacao)
    slot = await _slot_disponivel(provider, slot_id)

    codigos = {
        str(item.get("codigoExame") or "").strip().upper()
        for item in _json_itens(solicitacao.itens_exame)
        if item.get("codigoExame")
    }
    codigo_slot = str(slot.get("codigoExame") or "").strip().upper()
    if codigos and codigo_slot not in codigos:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "A vaga de destino não corresponde ao exame solicitado.",
        )

    if await _conflito_paciente(
        db,
        agendamento.paciente_chave or solicitacao.paciente_chave or "",
        parse_datetime(slot["inicio"]),
        parse_datetime(slot["fim"]),
        ignorar_agendamento_id=agendamento_id,
    ):
        raise _erro(
            status.HTTP_409_CONFLICT,
            "Já existe agendamento ativo para este paciente neste intervalo.",
        )

    anterior = await _agendamento_para_dict(db, agendamento, provider)
    agendamento.slot_id = slot_id
    agendamento.autor = autor
    await db.flush()
    atualizado = await _agendamento_para_dict(db, agendamento, provider)
    await _auditar(
        db,
        usuario=autor,
        categoria="NEGOCIO_CLINICO",
        acao="MOVER_PROPOSTA_AGENDA",
        recurso=f"agendamento:{agendamento_id}",
        anteriores=anterior,
        novos=atualizado,
        ip=ip,
    )
    return atualizado


async def registrar_nao_confirmacao(
    db: AsyncSession,
    provider: SlotProviderInterface,
    *,
    agendamento_id: str,
    justificativa: Optional[str],
    autor: str,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Registra que o paciente não confirmou e encaminha para reagendamento."""
    if not justificativa or not justificativa.strip():
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Justificativa é obrigatória para registrar a não confirmação.",
        )
    agendamento = await _buscar_agendamento(db, agendamento_id)
    if agendamento.status not in STATUS_OCUPANTES:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Somente propostas ou agendamentos ativos podem ser marcados como não confirmados.",
        )
    solicitacao = await _buscar_solicitacao(db, agendamento.solicitacao_id)
    status_anterior = solicitacao.status
    anterior = await _agendamento_para_dict(db, agendamento, provider)
    agendamento.status = "CANCELADO"
    agendamento.justificativa = justificativa.strip()
    agendamento.cancelado_em = _agora()
    agendamento.autor = autor
    solicitacao.status = STATUS_AGUARDANDO_REAGENDAMENTO
    solicitacao.atualizado_em = _agora()
    await db.flush()
    atualizado = await _agendamento_para_dict(db, agendamento, provider)
    await _auditar(
        db,
        usuario=autor,
        categoria="NEGOCIO_CLINICO",
        acao="REGISTRAR_NAO_CONFIRMACAO",
        recurso=f"agendamento:{agendamento_id}",
        anteriores={**anterior, "statusSolicitacao": status_anterior},
        novos={
            **atualizado,
            "statusSolicitacao": STATUS_AGUARDANDO_REAGENDAMENTO,
            "motivo": justificativa.strip(),
        },
        ip=ip,
    )
    return atualizado


# ---------------------------------------------------------------------------
# Edição em lote da fila de marcação
# ---------------------------------------------------------------------------

_STATUS_PARA_SOLICITACAO = {
    "ATIVO": STATUS_AGENDADA,
}


async def alterar_status_lote(
    db: AsyncSession,
    provider: SlotProviderInterface,
    *,
    agendamento_ids: List[str],
    novo_status: str,
    justificativa: Optional[str],
    autor: str,
    ip: Optional[str],
) -> Dict[str, Any]:
    """Altera o status de vários agendamentos de uma só vez (edição em lote).

    Todos os status são elegíveis. A justificativa é única para todo o lote.
    Cada alteração é auditada individualmente como `NEGOCIO_CLINICO`.
    Retorna a lista de itens processados com status anterior e novo.
    """
    if not agendamento_ids:
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Informe ao menos um agendamento para edição em lote.",
        )
    if not justificativa or not justificativa.strip():
        raise _erro(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Justificativa é obrigatória para edição em lote.",
        )

    processados: List[Dict[str, Any]] = []
    erros: List[Dict[str, str]] = []

    for agendamento_id in agendamento_ids:
        agendamento = await _buscar_agendamento(db, agendamento_id)
        status_anterior = agendamento.status

        anterior = await _agendamento_para_dict(db, agendamento, provider)
        agendamento.status = novo_status
        agendamento.justificativa = justificativa.strip()
        agendamento.autor = autor

        solicitacao = await _buscar_solicitacao(db, agendamento.solicitacao_id)
        status_solicitacao_anterior = solicitacao.status
        novo_status_solicitacao = _STATUS_PARA_SOLICITACAO.get(novo_status)
        if novo_status_solicitacao:
            solicitacao.status = novo_status_solicitacao
        solicitacao.atualizado_em = _agora()

        await db.flush()
        atualizado = await _agendamento_para_dict(db, agendamento, provider)

        await _auditar(
            db,
            usuario=autor,
            categoria="NEGOCIO_CLINICO",
            acao="ALTERAR_STATUS_LOTE",
            recurso=f"agendamento:{agendamento_id}",
            anteriores={
                **anterior,
                "statusSolicitacao": status_solicitacao_anterior,
            },
            novos={
                **atualizado,
                "statusSolicitacao": solicitacao.status,
                "motivo": justificativa.strip(),
            },
            ip=ip,
        )

        processados.append({
            "agendamentoId": agendamento_id,
            "statusAnterior": status_anterior,
            "statusNovo": novo_status,
            "protocolo": atualizado.get("protocolo", ""),
            "pacienteNome": atualizado.get("pacienteNome", ""),
        })

    if erros:
        raise _erro(
            status.HTTP_409_CONFLICT,
            f"{len(erros)} agendamento(ns) não pôde(m) ser alterado(s).",
        )

    return {
        "processados": len(processados),
        "novoStatus": novo_status,
        "itens": processados,
    }


# ---------------------------------------------------------------------------
# Consultas e sugestões
# ---------------------------------------------------------------------------

async def listar_calendario(
    db: AsyncSession,
    provider: SlotProviderInterface,
    *,
    de: Optional[str],
    ate: Optional[str],
    unidade: str,
    codigo_exame: str,
    paciente_chave: Optional[str],
) -> Dict[str, Any]:
    """Monta o contrato do calendário; ocupadas ignora o filtro de paciente."""
    inicio_padrao = _agora() - timedelta(days=1)
    fim_padrao = inicio_padrao + timedelta(days=settings.AGENDA_SUGGESTION_HORIZON_DAYS)
    de_dt = parse_datetime(de, inicio_padrao) if de else inicio_padrao
    ate_dt = parse_datetime(ate, fim_padrao) if ate else fim_padrao

    slots = await provider.listar(
        de=de_dt, ate=ate_dt, unidade=unidade, codigo_exame=codigo_exame
    )

    stmt = (
        select(Agendamento)
        .join(AgendaSlot, Agendamento.slot_id == AgendaSlot.id)
        .where(
            Agendamento.status.in_(STATUS_OCUPANTES),
            Agendamento.deleted_at.is_(None),
            AgendaSlot.fim >= para_utc_naive(de_dt),
            AgendaSlot.inicio <= para_utc_naive(ate_dt),
        )
    )
    if paciente_chave:
        stmt = stmt.where(Agendamento.paciente_chave == paciente_chave)
    agendamentos = (await db.scalars(stmt.order_by(AgendaSlot.inicio))).all()
    return {
        "de": para_iso(de_dt),
        "ate": para_iso(ate_dt),
        "slots": slots,
        "agendamentos": [
            await _agendamento_para_dict(db, agendamento, provider)
            for agendamento in agendamentos
        ],
    }


async def listar_por_paciente(
    db: AsyncSession, provider: SlotProviderInterface, paciente_chave: str
) -> List[Dict[str, Any]]:
    """Lista todos os status de um paciente, ordenados por dataHora desc."""
    agendamentos = (
        await db.scalars(
            select(Agendamento).where(
                Agendamento.paciente_chave == paciente_chave,
                Agendamento.deleted_at.is_(None),
            )
        )
    ).all()
    resultado = [
        await _agendamento_para_dict(db, agendamento, provider)
        for agendamento in agendamentos
    ]
    return sorted(
        resultado,
        key=lambda item: parse_datetime(item["dataHora"], datetime.min.replace(tzinfo=timezone.utc)),
        reverse=True,
    )


async def buscar_pacientes(db: AsyncSession, termo: str) -> List[Dict[str, Any]]:
    """Busca por prontuário/nome/protocolo, sem CPF/CNS nem endereço."""
    busca = f"%{termo.strip()}%"
    solicitacoes = (
        await db.scalars(
            select(Solicitacao)
            .where(
                Solicitacao.deleted_at.is_(None),
                or_(
                    Solicitacao.prontuario.ilike(busca),
                    Solicitacao.paciente_nome.ilike(busca),
                    Solicitacao.protocolo.ilike(busca),
                ),
            )
            .order_by(Solicitacao.paciente_nome)
            .limit(50)
        )
    ).all()
    contagens = dict(
        (
            await db.execute(
                select(Agendamento.paciente_chave, func.count(Agendamento.id))
                .where(
                    Agendamento.status == "ATIVO",
                    Agendamento.deleted_at.is_(None),
                )
                .group_by(Agendamento.paciente_chave)
            )
        ).all()
    )
    vistos: set[str] = set()
    resultado: List[Dict[str, Any]] = []
    for solicitacao in solicitacoes:
        chave = solicitacao.paciente_chave or ""
        if chave in vistos:
            continue
        vistos.add(chave)
        resultado.append(
            {
                "pacienteChave": chave,
                "pacienteNome": solicitacao.paciente_nome,
                "prontuario": solicitacao.prontuario,
                "agendamentosAtivos": int(contagens.get(chave, 0)),
            }
        )
    return resultado


async def _distancia_do_paciente(
    db: AsyncSession, paciente_chave: str
) -> tuple[Optional[float], str]:
    """Lê a última distância calculada; sem registro não inventa coordenadas."""
    endereco = await db.scalar(
        select(PacienteEndereco)
        .where(
            PacienteEndereco.paciente_chave == paciente_chave,
            PacienteEndereco.deleted_at.is_(None),
        )
        .order_by(PacienteEndereco.calculado_em.desc())
    )
    if not endereco or endereco.distancia_km is None:
        return None, "INDISPONIVEL"
    fonte = (endereco.distancia_fonte or "").upper()
    if fonte not in {"OSM", "MOCK"}:
        fonte = "INDISPONIVEL"
    return float(endereco.distancia_km), fonte


def _pesos() -> Dict[str, float]:
    """Pesos configuráveis normalizados para soma 100."""
    pesos = {
        "prioridade": max(0.0, float(settings.AGENDA_WEIGHT_PRIORIDADE)),
        "vagas": max(0.0, float(settings.AGENDA_WEIGHT_VAGAS)),
        "compatibilidade": max(0.0, float(settings.AGENDA_WEIGHT_COMPATIBILIDADE)),
        "espera": max(0.0, float(settings.AGENDA_WEIGHT_ESPERA)),
        "distancia": max(0.0, float(settings.AGENDA_WEIGHT_DISTANCIA)),
    }
    total = sum(pesos.values())
    if total <= 0:
        return {chave: valor / 5 for chave, valor in pesos.items()}
    return {chave: valor * 100 / total for chave, valor in pesos.items()}


async def listar_sugestoes(
    db: AsyncSession,
    provider: SlotProviderInterface,
    solicitacao_id: str,
    *,
    limite: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Sugere vagas por prioridade, vagas, compatibilidade, espera e distância."""
    solicitacao = await _buscar_solicitacao(db, solicitacao_id)
    ja_agendada = await db.scalar(
        select(Agendamento.id).where(
            Agendamento.solicitacao_id == solicitacao_id,
            Agendamento.status.in_(STATUS_OCUPANTES),
            Agendamento.deleted_at.is_(None),
        )
    )
    if ja_agendada:
        return []

    agora = _agora()
    horizonte = agora + timedelta(days=max(1, int(settings.AGENDA_SUGGESTION_HORIZON_DAYS)))
    slots = await provider.listar(de=agora, ate=horizonte)
    codigos = {
        str(item.get("codigoExame") or "").strip().upper()
        for item in _json_itens(solicitacao.itens_exame)
        if item.get("codigoExame")
    }

    distancia_km, distancia_fonte = await _distancia_do_paciente(
        db, solicitacao.paciente_chave or ""
    )
    pesos = _pesos()
    pontuacao_clinica = min(100.0, max(0.0, float(solicitacao.pontuacao or 0)))
    candidatos: List[Dict[str, Any]] = []

    for slot in slots:
        if slot["status"] != "DISPONIVEL" or slot["livres"] <= 0:
            continue
        inicio = para_utc_aware(parse_datetime(slot["inicio"]))
        fim = para_utc_aware(parse_datetime(slot["fim"]))
        if inicio < agora or inicio > horizonte:
            continue
        codigo_slot = str(slot["codigoExame"] or "").strip().upper()
        if codigo_slot and codigo_slot not in codigos:
            continue
        generico = not codigo_slot
        if await _conflito_paciente(
            db, solicitacao.paciente_chave or "", inicio, fim
        ):
            continue

        dias_espera = min(1.0, max(0.0, (inicio - agora).total_seconds() / 86400))
        razao_vagas = min(1.0, slot["livres"] / max(1, slot["capacidade"]))
        fator_distancia = (
            0.5
            if distancia_km is None
            else 1.0 - min(distancia_km, 50.0) / 50.0
        )
        compatibilidade = 0.5 if generico else 1.0
        nota = (
            pesos["prioridade"] * (pontuacao_clinica / 100)
            + pesos["vagas"] * razao_vagas
            + pesos["compatibilidade"] * compatibilidade
            + pesos["espera"] * (1.0 - dias_espera)
            + pesos["distancia"] * fator_distancia
        )
        motivos = [
            f"Prioridade clínica (pontuação {int(pontuacao_clinica)})",
            f"Vaga com {slot['livres']} livre(s) de {slot['capacidade']}",
            "Slot genérico compatível" if generico else f"Exame compatível ({codigo_slot})",
            f"Disponível em {dias_espera:.1f} dia(s)",
            (
                f"Distância de {distancia_km:.1f} km (fonte {distancia_fonte})"
                if distancia_km is not None and distancia_fonte != "INDISPONIVEL"
                else "Distância indisponível (peso neutro)"
            ),
        ]
        candidatos.append(
            {
                "slot": slot,
                "pontuacao": round(min(100.0, max(0.0, nota)), 1),
                "motivos": motivos,
                "distanciaKm": distancia_km,
                "distanciaOrigem": distancia_fonte,
            }
        )

    candidatos.sort(
        key=lambda item: (
            -item["pontuacao"],
            item["distanciaKm"] if item["distanciaKm"] is not None else float("inf"),
            item["slot"]["inicio"],
        )
    )
    total = int(limite) if limite is not None else int(settings.AGENDA_SUGGESTION_LIMIT)
    return candidatos[: max(1, total)]
