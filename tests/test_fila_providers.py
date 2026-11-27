"""
Testes dos provedores usados pela Fila de Exames (TASK-010)
==========================================================
- ``ExameCsvProvider.buscar_por_nome`` (busca ativa por nome no AGHU/CSV).
- ``FilaSqliteProvider`` retornando apenas regras ativas e não excluídas.
"""

import asyncio
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.models import IncompatibilidadeExame, RegraExame, RegraPrioridade
from src.providers.implementations.exame_csv_provider import ExameCsvProvider
from src.providers.implementations.fila_sqlite_provider import FilaSqliteProvider
from src.resources.database import Base
from src.resources.seed_exames import (
    INCOMPATIBILIDADES_EXAMES_INICIAIS,
    REGRAS_EXAMES_INICIAIS,
    REGRAS_PRIORIDADE_INICIAIS,
)

CSV_OFICIAL = "data/exames_aghu_mock.csv"


def test_csv_buscar_por_nome_parcial_sem_acento_e_caixa() -> None:
    provider = ExameCsvProvider(csv_path=CSV_OFICIAL)
    resultado = asyncio.run(provider.buscar_por_nome("anonimizado 01"))
    assert resultado
    assert {r["nome"] for r in resultado} == {"PACIENTE ANONIMIZADO 01"}


def test_csv_buscar_por_nome_curto_ou_inexistente_retorna_vazio() -> None:
    provider = ExameCsvProvider(csv_path=CSV_OFICIAL)
    assert asyncio.run(provider.buscar_por_nome("ab")) == []
    assert asyncio.run(provider.buscar_por_nome("nome que nao existe")) == []


def test_fila_provider_retorna_apenas_regras_ativas(tmp_path: Path) -> None:
    async def cenario() -> tuple[set[str], set[str], int]:
        engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'regras.db'}")
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            fabrica = async_sessionmaker(engine, expire_on_commit=False)
            async with fabrica() as session:
                session.add_all(RegraPrioridade(**r) for r in REGRAS_PRIORIDADE_INICIAIS)
                session.add_all(RegraExame(**r) for r in REGRAS_EXAMES_INICIAIS)
                await session.flush()
                session.add_all(IncompatibilidadeExame(**r) for r in INCOMPATIBILIDADES_EXAMES_INICIAIS)
                await session.commit()

                provider = FilaSqliteProvider(session)
                regras = {r["codigo"]: r for r in await provider.listar_regras_prioridade()}
                regras_obj = await session.get(RegraPrioridade, regras["CLINICA_ONCOLOGIA"]["id"])
                regras_obj.ativo = False
                transplante = await session.get(RegraPrioridade, regras["GRUPO_TRANSPLANTE"]["id"])
                transplante.deleted_at = datetime(2026, 11, 1)
                exames = {r["codigo_exame"]: r for r in await provider.listar_regras_exames()}
                (await session.get(RegraExame, exames["HEMO"]["id"])).ativo = False
                incompat = await provider.listar_incompatibilidades()
                (await session.get(IncompatibilidadeExame, incompat[0]["id"])).deleted_at = datetime(2026, 11, 1)
                await session.commit()

                return (
                    {r["codigo"] for r in await provider.listar_regras_prioridade()},
                    {r["codigo_exame"] for r in await provider.listar_regras_exames()},
                    len(await provider.listar_incompatibilidades()),
                )
        finally:
            await engine.dispose()

    prioridades, exames, total_incompat = asyncio.run(cenario())
    assert "CLINICA_ONCOLOGIA" not in prioridades and "GRUPO_TRANSPLANTE" not in prioridades
    assert "GRUPO_ROTINA" in prioridades
    assert "HEMO" not in exames and "COLONO" in exames
    assert total_incompat == len(INCOMPATIBILIDADES_EXAMES_INICIAIS) - 1
