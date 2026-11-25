"""
Seed Inicial Idempotente de Regras de Fila e Exames (`data/app.db`)
===================================================================
Popula no banco SQLite local da aplicação os cadastros iniciais configuráveis
especificados em ``docs/especificacao/04-modelo-dados.md`` e ``SPEC.md``
(TASK-005):

1. ``regras_prioridade``: pesos padrão de priorização clínica
   (Oncologia -> Transplante -> Hemodiálise -> Nefrologia -> Vulneráveis ->
   Retorno Próximo -> Afinidade Clínica × Exame -> Rotina).
2. ``regras_exames``: parâmetros operacionais e clínicos por sigla oficial do
   exame no AGHU (janelas de retorno de espirometria <= 10d/240h e INR <= 72h,
   alerta etário de mamografia >= 40 anos, preparo, jejum e prioridade matutina
   para diabéticos).
3. ``incompatibilidades_exames``: matriz inicial de pares incompatíveis
   (colonoscopia × sangue, ressonância × oftalmologia, etc.), inserida após
   ``regras_exames`` para satisfazer a chave estrangeira ``codigo_exame_origem``.

Uso via CLI::

    python -m src.resources.seed_exames
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import event, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import (  # noqa: F401 - garante registro completo em Base.metadata
    IncompatibilidadeExame,
    RegraExame,
    RegraPrioridade,
)
from .database import Base, DatabaseManager

logger = logging.getLogger("seed_exames")


# ---------------------------------------------------------------------------
# Catálogos declarativos iniciais (editáveis via /api/regras após o seed)
# ---------------------------------------------------------------------------

REGRAS_PRIORIDADE_INICIAIS: tuple[dict[str, Any], ...] = (
    {
        "codigo": "CLINICA_ONCOLOGIA",
        "nome": "Oncologia",
        "tipo_criterio": "CLINICA",
        "valor_match": "ONCOLOGIA",
        "peso": 100,
        "ativo": True,
        "descricao": (
            "Prioridade máxima para solicitações originadas pela Oncologia "
            "Clínica ou Cirúrgica."
        ),
    },
    {
        "codigo": "GRUPO_TRANSPLANTE",
        "nome": "Transplante",
        "tipo_criterio": "GRUPO_CLINICO",
        "valor_match": "TRANSPLANTE",
        "peso": 80,
        "ativo": True,
        "descricao": (
            "Alta prioridade para pacientes em pré-transplante ou "
            "acompanhamento pós-transplante."
        ),
    },
    {
        "codigo": "GRUPO_HEMODIALISE",
        "nome": "Hemodiálise",
        "tipo_criterio": "GRUPO_CLINICO",
        "valor_match": "HEMODIALISE",
        "peso": 75,
        "ativo": True,
        "descricao": (
            "Prioridade elevada para pacientes renais crônicos em regime "
            "de hemodiálise."
        ),
    },
    {
        "codigo": "CLINICA_NEFROLOGIA",
        "nome": "Nefrologia",
        "tipo_criterio": "CLINICA",
        "valor_match": "NEFROLOGIA",
        "peso": 65,
        "ativo": True,
        "descricao": (
            "Prioridade clínica para pacientes acompanhados pelo ambulatório "
            "de Nefrologia."
        ),
    },
    {
        "codigo": "VULNERAVEL_GESTANTE",
        "nome": "Gestante / Pré-Natal",
        "tipo_criterio": "VULNERAVEL",
        "valor_match": "GESTANTE,OBSTETRICIA,PRE-NATAL",
        "peso": 40,
        "ativo": True,
        "descricao": (
            "Grupo vulnerável prioritário: gestantes e solicitações de "
            "Obstetrícia / Pré-Natal."
        ),
    },
    {
        "codigo": "VULNERAVEL_CRIANCA",
        "nome": "Criança / Pediatria",
        "tipo_criterio": "VULNERAVEL",
        "valor_match": "CRIANCA,PEDIATRIA",
        "peso": 40,
        "ativo": True,
        "descricao": (
            "Grupo vulnerável prioritário: pacientes pediátricos e "
            "solicitações da Pediatria."
        ),
    },
    {
        "codigo": "VULNERAVEL_IDOSO",
        "nome": "Idoso (60+ anos)",
        "tipo_criterio": "VULNERAVEL",
        "valor_match": "IDOSO,GERIATRIA",
        "peso": 40,
        "ativo": True,
        "descricao": (
            "Grupo vulnerável prioritário: pacientes idosos (60+ anos) ou "
            "acompanhados pela Geriatria."
        ),
    },
    {
        "codigo": "RETORNO_PROXIMO_15D",
        "nome": "Retorno médico em até 15 dias",
        "tipo_criterio": "RETORNO_PROXIMO",
        "valor_match": "<=15",
        "peso": 20,
        "ativo": True,
        "descricao": (
            "Bônus de prioridade para pacientes cuja consulta de retorno "
            "médico ocorrerá em até 15 dias."
        ),
    },
    {
        "codigo": "AFINIDADE_CLINICA_EXAME",
        "nome": "Afinidade Clínica Solicitante × Exame",
        "tipo_criterio": "AFINIDADE_EXAME",
        "valor_match": "AFINIDADE_ESPECIALIDADE",
        "peso": 15,
        "ativo": True,
        "descricao": (
            "Bônus adicional quando há afinidade direta entre a clínica/"
            "especialidade solicitante e o exame solicitado."
        ),
    },
    {
        "codigo": "GRUPO_ROTINA",
        "nome": "Rotina Ambulatorial",
        "tipo_criterio": "GRUPO_CLINICO",
        "valor_match": "ROTINA",
        "peso": 10,
        "ativo": True,
        "descricao": (
            "Peso base padrão para solicitações ambulatoriais de rotina sem "
            "critério clínico prioritário."
        ),
    },
)

REGRAS_EXAMES_INICIAIS: tuple[dict[str, Any], ...] = (
    {
        "codigo_exame": "ESPIRO",
        "nome_exame": "ESPIROMETRIA COMPLETA COM PROVA BRONCODILATADORA",
        "unidade_executora": "PNEUMOLOGIA / PROVA DE FUNCAO PULMONAR",
        "antecedencia_minima_dias": 1,
        "janela_retorno_max_horas": 240,
        "exige_jejum": False,
        "priorizar_manha_diabetico": False,
        "idade_minima_alerta": None,
        "orientacoes_preparo": (
            "Realizar até 10 dias (240h) antes da consulta de retorno. "
            "Suspender broncodilatadores conforme prescrição médica e evitar "
            "cafeína ou tabagismo nas 6 horas anteriores."
        ),
        "ativo": True,
    },
    {
        "codigo_exame": "INR",
        "nome_exame": "COAGULOGRAMA / TEMPO DE PROTROMBINA (INR)",
        "unidade_executora": "LABORATORIO DE ANALISES CLINICAS",
        "antecedencia_minima_dias": 0,
        "janela_retorno_max_horas": 72,
        "exige_jejum": True,
        "priorizar_manha_diabetico": True,
        "idade_minima_alerta": None,
        "orientacoes_preparo": (
            "Realizar em até 72 horas antes do retorno médico. Jejum "
            "recomendado de 4 a 8 horas; priorizar os primeiros horários da "
            "manhã para pacientes diabéticos."
        ),
        "ativo": True,
    },
    {
        "codigo_exame": "RXMM1",
        "nome_exame": "MAMOGRAFIA BILATERAL DIGITAL",
        "unidade_executora": "UDI: MAMOGRAFIA",
        "antecedencia_minima_dias": 0,
        "janela_retorno_max_horas": None,
        "exige_jejum": False,
        "priorizar_manha_diabetico": False,
        "idade_minima_alerta": 40,
        "orientacoes_preparo": (
            "Alerta de rastreamento mamográfico para faixa etária a partir de "
            "40 anos. Não aplicar desodorante, talco, cremes ou óleos nas "
            "mamas e axilas no dia do exame; levar exames anteriores."
        ),
        "ativo": True,
    },
    {
        "codigo_exame": "COLONO",
        "nome_exame": "COLONOSCOPIA COM BIOPSIA, SE NECESSARIO",
        "unidade_executora": "ENDOSCOPIA DIGESTIVA / GASTROENTEROLOGIA",
        "antecedencia_minima_dias": 3,
        "janela_retorno_max_horas": None,
        "exige_jejum": True,
        "priorizar_manha_diabetico": True,
        "idade_minima_alerta": None,
        "orientacoes_preparo": (
            "Exige antecedência mínima para preparo intestinal rigoroso "
            "(48h a 72h antes), jejum absoluto conforme protocolo e presença "
            "de acompanhante adulto. Priorizar primeiros horários da manhã "
            "para pacientes diabéticos."
        ),
        "ativo": True,
    },
    {
        "codigo_exame": "HEMO",
        "nome_exame": "HEMOGRAMA COMPLETO / EXAME DE SANGUE",
        "unidade_executora": "LABORATORIO DE ANALISES CLINICAS",
        "antecedencia_minima_dias": 0,
        "janela_retorno_max_horas": None,
        "exige_jejum": True,
        "priorizar_manha_diabetico": True,
        "idade_minima_alerta": None,
        "orientacoes_preparo": (
            "Jejum de 8 a 12 horas conforme bateria laboratorial solicitada "
            "(ingestão moderada de água permitida). Priorizar os primeiros "
            "horários da manhã para pacientes diabéticos."
        ),
        "ativo": True,
    },
    {
        "codigo_exame": "RMCRAN",
        "nome_exame": "RESSONANCIA MAGNETICA DE CRANIO COM CONTRASTE",
        "unidade_executora": "UDI: RESSONANCIA MAGNETICA",
        "antecedencia_minima_dias": 2,
        "janela_retorno_max_horas": None,
        "exige_jejum": True,
        "priorizar_manha_diabetico": True,
        "idade_minima_alerta": None,
        "orientacoes_preparo": (
            "Jejum de 4 a 6 horas quando houver uso de contraste gadolínio. "
            "Checar ausência de implantes ferromagnéticos ou marca-passo e "
            "apresentar exame recente de função renal (creatinina)."
        ),
        "ativo": True,
    },
    {
        "codigo_exame": "OFTALM",
        "nome_exame": "MAPEAMENTO DE RETINA BILATERAL",
        "unidade_executora": "OFTALMOLOGIA",
        "antecedencia_minima_dias": 0,
        "janela_retorno_max_horas": None,
        "exige_jejum": False,
        "priorizar_manha_diabetico": False,
        "idade_minima_alerta": None,
        "orientacoes_preparo": (
            "Procedimento realizado com dilatação pupilar (midríase). "
            "Recomenda-se comparecer com acompanhante, levar óculos escuros "
            "e não dirigir após o exame."
        ),
        "ativo": True,
    },
    {
        "codigo_exame": "USAX",
        "nome_exame": "ULTRASSONOGRAFIA DE ABDOME TOTAL",
        "unidade_executora": "UDI: ULTRASSONOGRAFIA",
        "antecedencia_minima_dias": 1,
        "janela_retorno_max_horas": None,
        "exige_jejum": True,
        "priorizar_manha_diabetico": True,
        "idade_minima_alerta": None,
        "orientacoes_preparo": (
            "Jejum de 6 a 8 horas e repleção vesical (bexiga cheia) para "
            "avaliação abdominal/pélvica. Priorizar os primeiros horários "
            "da manhã para pacientes diabéticos."
        ),
        "ativo": True,
    },
    {
        "codigo_exame": "TCABD",
        "nome_exame": "TOMOGRAFIA COMPUTADORIZADA DE ABDOME E PELVE",
        "unidade_executora": "UDI: TOMOGRAFIA COMPUTADORIZADA",
        "antecedencia_minima_dias": 2,
        "janela_retorno_max_horas": None,
        "exige_jejum": True,
        "priorizar_manha_diabetico": True,
        "idade_minima_alerta": None,
        "orientacoes_preparo": (
            "Jejum de 4 a 6 horas. Confirmar função renal (creatinina), "
            "histórico alérgico a contraste iodado e orientação médica sobre "
            "suspensão temporária de metformina em diabéticos."
        ),
        "ativo": True,
    },
    {
        "codigo_exame": "CMDIP",
        "nome_exame": "CINTILOGRAFIA MIOCARDICA (ESTRESSE FARMACOLOGICO, DIPIRIDAMOL)",
        "unidade_executora": "UDI: MEDICINA NUCLEAR",
        "antecedencia_minima_dias": 2,
        "janela_retorno_max_horas": None,
        "exige_jejum": True,
        "priorizar_manha_diabetico": True,
        "idade_minima_alerta": None,
        "orientacoes_preparo": (
            "Suspender café, chás escuros, chocolates, refrigerantes à base "
            "de cola e medicamentos com xantinas 24h antes. Jejum leve de "
            "4 horas; priorizar horários matutinos para diabéticos."
        ),
        "ativo": True,
    },
)

INCOMPATIBILIDADES_EXAMES_INICIAIS: tuple[dict[str, Any], ...] = (
    {
        "codigo_exame_origem": "COLONO",
        "codigo_exame_conflitante": "HEMO",
        "tipo_conflito": "PREPARO",
        "intervalo_minimo_dias": 2,
        "motivo": (
            "O preparo intestinal e o jejum prolongado da colonoscopia "
            "interferem na coleta e nos parâmetros laboratoriais de exames "
            "de sangue no mesmo período."
        ),
        "ativo": True,
    },
    {
        "codigo_exame_origem": "COLONO",
        "codigo_exame_conflitante": "INR",
        "tipo_conflito": "PREPARO",
        "intervalo_minimo_dias": 2,
        "motivo": (
            "O preparo intestinal da colonoscopia conflita com a coleta de "
            "coagulograma/INR no mesmo dia ou em intervalo inferior a 48h."
        ),
        "ativo": True,
    },
    {
        "codigo_exame_origem": "RMCRAN",
        "codigo_exame_conflitante": "OFTALM",
        "tipo_conflito": "MESMO_DIA",
        "intervalo_minimo_dias": 1,
        "motivo": (
            "A dilatação pupilar (midríase) do exame oftalmológico e a "
            "logística de contraste/sedação da ressonância magnética impedem "
            "o agendamento de ambos no mesmo dia."
        ),
        "ativo": True,
    },
    {
        "codigo_exame_origem": "COLONO",
        "codigo_exame_conflitante": "USAX",
        "tipo_conflito": "PREPARO",
        "intervalo_minimo_dias": 1,
        "motivo": (
            "A insuflação gasosa intestinal e o preparo da colonoscopia "
            "prejudicam a janela acústica da ultrassonografia de abdome "
            "no mesmo dia."
        ),
        "ativo": True,
    },
    {
        "codigo_exame_origem": "TCABD",
        "codigo_exame_conflitante": "RMCRAN",
        "tipo_conflito": "INTERVALO_MINIMO",
        "intervalo_minimo_dias": 2,
        "motivo": (
            "Evitar sobrecarga renal por administração sequencial de meios "
            "de contraste (iodado e gadolínio) em intervalo inferior a 48h."
        ),
        "ativo": True,
    },
    {
        "codigo_exame_origem": "CMDIP",
        "codigo_exame_conflitante": "ESPIRO",
        "tipo_conflito": "MESMO_DIA",
        "intervalo_minimo_dias": 1,
        "motivo": (
            "O estresse farmacológico com dipiridamol e o uso de "
            "broncodilatadores na espirometria apresentam interferência "
            "clínica quando agendados no mesmo dia."
        ),
        "ativo": True,
    },
)


def _enable_sqlite_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
    """Ativa ``PRAGMA foreign_keys=ON`` em conexões SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def _resolver_app_db_url(dsn: Optional[str] = None) -> str:
    """
    Resolve o DSN do banco de dados local da aplicação (SQLite), seguindo a
    mesma precedência de ``src/main.py`` e ``src/config.py``.
    """
    if dsn:
        return dsn
    return (
        os.getenv("SQLITE_DSN")
        or os.getenv("APP_DB_URL")
        or settings.APP_DB_URL
    )


def _garantir_diretorio_sqlite(dsn: str) -> None:
    """Garante a existência do diretório pai quando o DSN aponta para arquivo SQLite."""
    url = make_url(dsn)
    if not url.drivername.startswith("sqlite"):
        return
    if not url.database or url.database == ":memory:":
        return
    parent = Path(url.database).parent
    if str(parent) and str(parent) != ".":
        parent.mkdir(parents=True, exist_ok=True)


async def seed_regras_iniciais(session: AsyncSession) -> dict[str, int]:
    """
    Popula de forma estritamente idempotente as regras iniciais de prioridade,
    regras por exame e matriz de incompatibilidades no banco local da aplicação.

    Ordem de execução garantida:
    1. ``RegraPrioridade`` (verificação de unicidade por ``codigo``);
    2. ``RegraExame`` (verificação de unicidade por ``codigo_exame`` + ``flush``);
    3. ``IncompatibilidadeExame`` (após ``RegraExame`` para satisfazer a FK
       ``codigo_exame_origem``, evitando duplicação do par origem × conflitante).

    Registros já existentes (inclusive editados ou excluídos logicamente via
    ``deleted_at``) são preservados sem sobrescrita nem duplicação.

    Args:
        session: Sessão assíncrona ativa do SQLAlchemy conectada ao banco local.

    Returns:
        Dicionário com a contagem de novos registros inseridos em cada tabela:
        ``{"regras_prioridade": int, "regras_exames": int, "incompatibilidades_exames": int}``.
    """
    # 1. Seed idempotente de RegraPrioridade (chave única: codigo)
    codigos_prioridade_existentes = set(
        (await session.scalars(select(RegraPrioridade.codigo))).all()
    )
    novas_prioridades: list[RegraPrioridade] = []
    for item in REGRAS_PRIORIDADE_INICIAIS:
        if item["codigo"] not in codigos_prioridade_existentes:
            novas_prioridades.append(RegraPrioridade(**item))
            codigos_prioridade_existentes.add(item["codigo"])
    if novas_prioridades:
        session.add_all(novas_prioridades)

    # 2. Seed idempotente de RegraExame (chave única: codigo_exame)
    codigos_exames_existentes = set(
        (await session.scalars(select(RegraExame.codigo_exame))).all()
    )
    novas_regras_exames: list[RegraExame] = []
    for item in REGRAS_EXAMES_INICIAIS:
        if item["codigo_exame"] not in codigos_exames_existentes:
            novas_regras_exames.append(RegraExame(**item))
            codigos_exames_existentes.add(item["codigo_exame"])
    if novas_regras_exames:
        session.add_all(novas_regras_exames)

    # Flush obrigatório antes de inserir IncompatibilidadeExame (FK codigo_exame_origem)
    await session.flush()

    # 3. Seed idempotente de IncompatibilidadeExame (par origem × conflitante)
    pares_existentes_rows = (
        await session.execute(
            select(
                IncompatibilidadeExame.codigo_exame_origem,
                IncompatibilidadeExame.codigo_exame_conflitante,
            )
        )
    ).all()
    pares_existentes: set[tuple[str, str]] = {
        (row[0], row[1]) for row in pares_existentes_rows
    }

    novas_incompatibilidades: list[IncompatibilidadeExame] = []
    for item in INCOMPATIBILIDADES_EXAMES_INICIAIS:
        origem = item["codigo_exame_origem"]
        conflitante = item["codigo_exame_conflitante"]
        if origem not in codigos_exames_existentes:
            continue
        if (origem, conflitante) in pares_existentes or (
            conflitante,
            origem,
        ) in pares_existentes:
            continue
        novas_incompatibilidades.append(IncompatibilidadeExame(**item))
        pares_existentes.add((origem, conflitante))

    if novas_incompatibilidades:
        session.add_all(novas_incompatibilidades)

    await session.commit()

    return {
        "regras_prioridade": len(novas_prioridades),
        "regras_exames": len(novas_regras_exames),
        "incompatibilidades_exames": len(novas_incompatibilidades),
    }


async def executar_seed_cli(dsn: Optional[str] = None) -> dict[str, int]:
    """
    Executa o seed inicial conectando-se ao banco de dados local da aplicação
    via ``DatabaseManager``.

    Args:
        dsn: URL assíncrona opcional do banco de dados. Quando omitida, utiliza
            ``SQLITE_DSN``, ``APP_DB_URL`` ou ``settings.APP_DB_URL``.

    Returns:
        Dicionário com a quantidade de novos registros inseridos por tabela.
    """
    db_url = _resolver_app_db_url(dsn)
    _garantir_diretorio_sqlite(db_url)

    db_manager = DatabaseManager(db_url)
    if make_url(db_url).drivername.startswith("sqlite"):
        event.listen(
            db_manager.engine.sync_engine,
            "connect",
            _enable_sqlite_foreign_keys,
        )

    try:
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        resultado: dict[str, int] = {
            "regras_prioridade": 0,
            "regras_exames": 0,
            "incompatibilidades_exames": 0,
        }
        async for session in db_manager.get_session():
            resultado = await seed_regras_iniciais(session)
            break
        return resultado
    finally:
        await db_manager.close_connection()


def main() -> None:
    """Ponto de entrada CLI para ``python -m src.resources.seed_exames``."""
    resultado = asyncio.run(executar_seed_cli())
    print(
        "Seed inicial concluído com sucesso: "
        f"regras_prioridade=+{resultado['regras_prioridade']}, "
        f"regras_exames=+{resultado['regras_exames']}, "
        f"incompatibilidades_exames=+{resultado['incompatibilidades_exames']}"
    )


if __name__ == "__main__":
    main()
