"""
Suíte de Testes das Migrações Alembic e do Seed Inicial de Exames
=================================================================
Valida ponta a ponta os entregáveis da TASK-005:

1. Ciclo completo de migração Alembic em banco SQLite isolado (``tmp_path``):
   ``upgrade head`` -> inspeção de tabelas, colunas, índices e chaves
   estrangeiras -> ``downgrade`` para revisão anterior -> ``upgrade head``.
2. Execução do seed ``seed_regras_iniciais(session)`` sobre banco migrado
   com ``PRAGMA foreign_keys=ON``, validando pesos de prioridade, regras de
   exames (espirometria <= 240h, INR <= 72h, mamografia >= 40 anos, preparo/jejum)
   e matriz de incompatibilidades respeitando a FK ``codigo_exame_origem``.
3. Idempotência estrita ao executar ``seed_regras_iniciais(session)`` e
   ``executar_seed_cli(dsn=...)`` múltiplas vezes (zero duplicidades, contagens
   estáveis e preservação de edições/exclusões lógicas).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, event, func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.models import (
    IncompatibilidadeExame,
    RegraExame,
    RegraPrioridade,
)
from src.resources.database import Base
from src.resources.seed_exames import (
    INCOMPATIBILIDADES_EXAMES_INICIAIS,
    REGRAS_EXAMES_INICIAIS,
    REGRAS_PRIORIDADE_INICIAIS,
    executar_seed_cli,
    seed_regras_iniciais,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI_PATH = REPO_ROOT / "alembic.ini"
ALEMBIC_DIR_PATH = REPO_ROOT / "alembic"

PREVIOUS_REVISION = "8a2efbe37bb6"
HEAD_REVISION = "c4f9b2a1e830"

EXPECTED_NEW_TABLES = {
    "importacoes_forms",
    "acompanhamento_fila",
    "regras_prioridade",
    "regras_exames",
    "incompatibilidades_exames",
}

EXPECTED_INDEXES_BY_TABLE: dict[str, set[str]] = {
    "importacoes_forms": {
        "ix_importacoes_forms_id",
        "ix_importacoes_forms_importado_em",
        "ix_importacoes_forms_usuario_importador",
        "ix_importacoes_forms_deleted_at",
    },
    "regras_prioridade": {
        "ix_regras_prioridade_id",
        "ix_regras_prioridade_codigo",
        "ix_regras_prioridade_tipo_criterio",
        "ix_regras_prioridade_ativo",
        "ix_regras_prioridade_deleted_at",
    },
    "regras_exames": {
        "ix_regras_exames_id",
        "ix_regras_exames_codigo_exame",
        "ix_regras_exames_unidade_executora",
        "ix_regras_exames_ativo",
        "ix_regras_exames_deleted_at",
    },
    "acompanhamento_fila": {
        "ix_acompanhamento_fila_id",
        "ix_acompanhamento_fila_importacao_id",
        "ix_acompanhamento_fila_codigo_solicitacao",
        "ix_acompanhamento_fila_codigo_exame",
        "ix_acompanhamento_fila_prontuario",
        "ix_acompanhamento_fila_nome_paciente",
        "ix_acompanhamento_fila_municipio",
        "ix_acompanhamento_fila_regiao_geografica",
        "ix_acompanhamento_fila_utiliza_tfd",
        "ix_acompanhamento_fila_data_retorno_medico",
        "ix_acompanhamento_fila_unidade_solicitante",
        "ix_acompanhamento_fila_especialidade_solicitante",
        "ix_acompanhamento_fila_status_higienizacao",
        "ix_acompanhamento_fila_status_operacional",
        "ix_acompanhamento_fila_prazo_confirmacao_em",
        "ix_acompanhamento_fila_data_agendada_aghu",
        "ix_acompanhamento_fila_created_at",
        "ix_acompanhamento_fila_deleted_at",
        "ix_acompanhamento_fila_prontuario_exame",
        "ix_acompanhamento_fila_solicitacao_exame",
        "ix_acompanhamento_fila_status_ativos",
    },
    "incompatibilidades_exames": {
        "ix_incompatibilidades_exames_id",
        "ix_incompatibilidades_exames_codigo_exame_origem",
        "ix_incompatibilidades_exames_codigo_exame_conflitante",
        "ix_incompatibilidades_exames_tipo_conflito",
        "ix_incompatibilidades_exames_ativo",
        "ix_incompatibilidades_exames_deleted_at",
        "ix_incompatibilidades_exames_par",
    },
}


def _enable_sqlite_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
    """Ativa ``PRAGMA foreign_keys=ON`` em conexões SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def _build_alembic_config(db_url: str) -> Config:
    """Constroi um ``alembic.config.Config`` apontando para o banco isolado."""
    cfg = Config(str(ALEMBIC_INI_PATH))
    cfg.set_main_option("script_location", str(ALEMBIC_DIR_PATH))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _get_alembic_version(db_path: Path) -> str | None:
    """Lê a revisão atual gravada na tabela ``alembic_version`` do SQLite."""
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    try:
        with engine.connect() as conn:
            return conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
    finally:
        engine.dispose()


def _assert_migrated_schema(db_path: Path) -> None:
    """Valida tabelas, colunas, índices e FKs esperados no banco SQLite migrado."""
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        assert EXPECTED_NEW_TABLES.issubset(existing_tables)

        # Paridade de colunas com os modelos SQLAlchemy registrados em Base.metadata
        for table_name in EXPECTED_NEW_TABLES:
            db_columns = {col["name"] for col in inspector.get_columns(table_name)}
            model_columns = set(Base.metadata.tables[table_name].columns.keys())
            assert db_columns == model_columns, (
                f"Colunas divergentes na tabela {table_name}: "
                f"db={db_columns} vs model={model_columns}"
            )

        # Validação de índices (incluindo índices compostos e únicos)
        for table_name, expected_indexes in EXPECTED_INDEXES_BY_TABLE.items():
            index_map = {idx["name"]: idx for idx in inspector.get_indexes(table_name)}
            assert expected_indexes.issubset(set(index_map.keys())), (
                f"Índices ausentes na tabela {table_name}: "
                f"{expected_indexes - set(index_map.keys())}"
            )

        regras_prio_indexes = {
            idx["name"]: idx for idx in inspector.get_indexes("regras_prioridade")
        }
        assert bool(regras_prio_indexes["ix_regras_prioridade_codigo"]["unique"]) is True

        regras_exames_indexes = {
            idx["name"]: idx for idx in inspector.get_indexes("regras_exames")
        }
        assert bool(regras_exames_indexes["ix_regras_exames_codigo_exame"]["unique"]) is True

        # Validação das chaves estrangeiras esperadas
        fila_fks = inspector.get_foreign_keys("acompanhamento_fila")
        assert any(
            fk["constrained_columns"] == ["importacao_id"]
            and fk["referred_table"] == "importacoes_forms"
            and fk["referred_columns"] == ["id"]
            for fk in fila_fks
        )

        incomp_fks = inspector.get_foreign_keys("incompatibilidades_exames")
        assert any(
            fk["constrained_columns"] == ["codigo_exame_origem"]
            and fk["referred_table"] == "regras_exames"
            and fk["referred_columns"] == ["codigo_exame"]
            for fk in incomp_fks
        )
    finally:
        engine.dispose()


def test_alembic_cadeia_de_revisoes() -> None:
    """Garante que a cadeia de revisões Alembic possui head único esperado."""
    cfg = _build_alembic_config("sqlite:///:memory:")
    script = ScriptDirectory.from_config(cfg)
    assert script.get_heads() == [HEAD_REVISION]

    head_rev = script.get_revision(HEAD_REVISION)
    assert head_rev is not None
    assert head_rev.down_revision == PREVIOUS_REVISION


def test_alembic_upgrade_downgrade_e_reupgrade_sqlite(tmp_path: Path) -> None:
    """
    Valida ``alembic upgrade head`` em SQLite novo (``tmp_path``), verifica
    tabelas/índices/FKs e constraints em tempo de execução, faz ``downgrade``
    para a revisão anterior e aplica ``upgrade head`` novamente.
    """
    db_path = tmp_path / "alembic_lifecycle.db"
    cfg = _build_alembic_config(f"sqlite:///{db_path}")

    # 1. Upgrade inicial até head
    command.upgrade(cfg, "head")
    assert db_path.exists()
    assert _get_alembic_version(db_path) == HEAD_REVISION
    _assert_migrated_schema(db_path)

    # 2. Valida enforcement real de FK com PRAGMA foreign_keys=ON no schema migrado
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    try:
        with engine.begin() as conn:
            assert conn.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
            with pytest.raises(IntegrityError):
                conn.execute(
                    text(
                        "INSERT INTO incompatibilidades_exames "
                        "(codigo_exame_origem, codigo_exame_conflitante, tipo_conflito, "
                        "intervalo_minimo_dias, motivo, ativo) "
                        "VALUES ('INEXISTENTE', 'HEMO', 'PREPARO', 1, 'Teste FK', 1)"
                    )
                )
        with engine.begin() as conn:
            with pytest.raises(IntegrityError):
                conn.execute(
                    text(
                        "INSERT INTO acompanhamento_fila "
                        "(importacao_id, codigo_solicitacao, nome_paciente, "
                        "created_at, updated_at) "
                        "VALUES (999999, 'SOL-FK-ERR', 'PACIENTE TESTE', "
                        "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                    )
                )
    finally:
        engine.dispose()

    # 3. Downgrade para revisão anterior deve remover todas as 5 novas tabelas
    command.downgrade(cfg, PREVIOUS_REVISION)
    assert _get_alembic_version(db_path) == PREVIOUS_REVISION

    engine = create_engine(f"sqlite:///{db_path}", future=True)
    try:
        tables_after_downgrade = set(inspect(engine).get_table_names())
        assert EXPECTED_NEW_TABLES.isdisjoint(tables_after_downgrade)
    finally:
        engine.dispose()

    # 4. Re-upgrade para head deve recriar tudo de forma limpa
    command.upgrade(cfg, "head")
    assert _get_alembic_version(db_path) == HEAD_REVISION
    _assert_migrated_schema(db_path)


def test_alembic_upgrade_async_url_sqlite(tmp_path: Path) -> None:
    """Valida que ``alembic/env.py`` também suporta URL ``sqlite+aiosqlite://``."""
    db_path = tmp_path / "alembic_async.db"
    cfg = _build_alembic_config(f"sqlite+aiosqlite:///{db_path}")

    command.upgrade(cfg, "head")
    assert _get_alembic_version(db_path) == HEAD_REVISION
    _assert_migrated_schema(db_path)

    command.downgrade(cfg, PREVIOUS_REVISION)
    assert _get_alembic_version(db_path) == PREVIOUS_REVISION

    command.upgrade(cfg, "head")
    assert _get_alembic_version(db_path) == HEAD_REVISION
    _assert_migrated_schema(db_path)


@pytest.mark.asyncio
async def test_seed_regras_iniciais_popula_tabelas_com_fk_ativa(tmp_path: Path) -> None:
    """
    Valida que ``seed_regras_iniciais(session)`` popula ``regras_prioridade``,
    ``regras_exames`` (incluindo espirometria, INR e mamografia) e
    ``incompatibilidades_exames`` em um banco migrado via Alembic com
    ``PRAGMA foreign_keys=ON``.
    """
    db_path = tmp_path / "seed_migrated.db"
    cfg = _build_alembic_config(f"sqlite:///{db_path}")
    command.upgrade(cfg, "head")

    async_engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    event.listen(async_engine.sync_engine, "connect", _enable_sqlite_foreign_keys)
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        async with session_factory() as session:
            fk_status = (await session.execute(text("PRAGMA foreign_keys"))).scalar_one()
            assert fk_status == 1

            resultado = await seed_regras_iniciais(session)
            assert resultado == {
                "regras_prioridade": len(REGRAS_PRIORIDADE_INICIAIS),
                "regras_exames": len(REGRAS_EXAMES_INICIAIS),
                "incompatibilidades_exames": len(INCOMPATIBILIDADES_EXAMES_INICIAIS),
            }

            # 1. Valida regras de prioridade e ordenação hierárquica esperada
            prioridades = list((await session.scalars(select(RegraPrioridade))).all())
            assert len(prioridades) == len(REGRAS_PRIORIDADE_INICIAIS)
            prioridade_por_codigo = {item.codigo: item for item in prioridades}

            assert prioridade_por_codigo["CLINICA_ONCOLOGIA"].peso == 100
            assert prioridade_por_codigo["GRUPO_TRANSPLANTE"].peso == 80
            assert prioridade_por_codigo["GRUPO_HEMODIALISE"].peso == 75
            assert prioridade_por_codigo["CLINICA_NEFROLOGIA"].peso == 65
            assert prioridade_por_codigo["VULNERAVEL_GESTANTE"].peso == 40
            assert prioridade_por_codigo["VULNERAVEL_CRIANCA"].peso == 40
            assert prioridade_por_codigo["VULNERAVEL_IDOSO"].peso == 40
            assert prioridade_por_codigo["RETORNO_PROXIMO_15D"].peso == 20
            assert prioridade_por_codigo["AFINIDADE_CLINICA_EXAME"].peso == 15
            assert prioridade_por_codigo["GRUPO_ROTINA"].peso == 10

            assert (
                prioridade_por_codigo["CLINICA_ONCOLOGIA"].peso
                > prioridade_por_codigo["GRUPO_TRANSPLANTE"].peso
                > prioridade_por_codigo["GRUPO_HEMODIALISE"].peso
                > prioridade_por_codigo["CLINICA_NEFROLOGIA"].peso
                > prioridade_por_codigo["VULNERAVEL_IDOSO"].peso
                > prioridade_por_codigo["GRUPO_ROTINA"].peso
            )

            # 2. Valida regras de exames obrigatórias da especificação
            regras_exames = list((await session.scalars(select(RegraExame))).all())
            assert len(regras_exames) == len(REGRAS_EXAMES_INICIAIS)
            exame_por_codigo = {item.codigo_exame: item for item in regras_exames}

            # Espirometria <= 10 dias (240h)
            espiro = exame_por_codigo["ESPIRO"]
            assert espiro.janela_retorno_max_horas == 240
            assert espiro.ativo is True

            # INR <= 72h
            inr = exame_por_codigo["INR"]
            assert inr.janela_retorno_max_horas == 72
            assert inr.exige_jejum is True
            assert inr.priorizar_manha_diabetico is True

            # Mamografia com alerta de faixa etária >= 40 anos
            mamo = exame_por_codigo["RXMM1"]
            assert mamo.idade_minima_alerta == 40
            assert "MAMOGRAFIA" in mamo.nome_exame.upper()

            # Regras complementares (colonoscopia, sangue/jejum, ressonância, oftalmo)
            assert exame_por_codigo["COLONO"].antecedencia_minima_dias >= 1
            assert exame_por_codigo["COLONO"].exige_jejum is True
            assert exame_por_codigo["HEMO"].exige_jejum is True
            assert exame_por_codigo["HEMO"].priorizar_manha_diabetico is True
            assert "RMCRAN" in exame_por_codigo
            assert "OFTALM" in exame_por_codigo

            # 3. Valida incompatibilidades iniciais e integridade referencial
            incompatibilidades = list(
                (await session.scalars(select(IncompatibilidadeExame))).all()
            )
            assert len(incompatibilidades) == len(INCOMPATIBILIDADES_EXAMES_INICIAIS)
            pares = {
                (item.codigo_exame_origem, item.codigo_exame_conflitante): item
                for item in incompatibilidades
            }

            assert ("COLONO", "HEMO") in pares
            assert pares[("COLONO", "HEMO")].tipo_conflito == "PREPARO"
            assert ("COLONO", "INR") in pares
            assert ("RMCRAN", "OFTALM") in pares
            assert pares[("RMCRAN", "OFTALM")].tipo_conflito == "MESMO_DIA"

            for item in incompatibilidades:
                assert item.codigo_exame_origem in exame_por_codigo

            # Confirma que a FK continua bloqueando código de origem inexistente
            session.add(
                IncompatibilidadeExame(
                    codigo_exame_origem="CODIGO_INEXISTENTE",
                    codigo_exame_conflitante="HEMO",
                    tipo_conflito="MESMO_DIA",
                    intervalo_minimo_dias=1,
                    motivo="Teste de integridade referencial",
                    ativo=True,
                )
            )
            with pytest.raises(IntegrityError):
                await session.commit()
            await session.rollback()
    finally:
        await async_engine.dispose()


@pytest.mark.asyncio
async def test_seed_regras_iniciais_estritamente_idempotente(tmp_path: Path) -> None:
    """
    Executar ``seed_regras_iniciais(session)`` duas vezes (e novamente após
    edição/exclusão lógica) não gera duplicidades e mantém contagens estáveis.
    """
    db_path = tmp_path / "seed_idempotent.db"
    cfg = _build_alembic_config(f"sqlite:///{db_path}")
    command.upgrade(cfg, "head")

    async_engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    event.listen(async_engine.sync_engine, "connect", _enable_sqlite_foreign_keys)
    session_factory = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        # 1ª execução: popula todos os registros iniciais
        async with session_factory() as session:
            primeira = await seed_regras_iniciais(session)
            assert primeira == {
                "regras_prioridade": len(REGRAS_PRIORIDADE_INICIAIS),
                "regras_exames": len(REGRAS_EXAMES_INICIAIS),
                "incompatibilidades_exames": len(INCOMPATIBILIDADES_EXAMES_INICIAIS),
            }

        # 2ª execução em nova sessão: zero inserções novas e contagens inalteradas
        async with session_factory() as session:
            segunda = await seed_regras_iniciais(session)
            assert segunda == {
                "regras_prioridade": 0,
                "regras_exames": 0,
                "incompatibilidades_exames": 0,
            }

            total_prio = await session.scalar(select(func.count(RegraPrioridade.id)))
            total_exames = await session.scalar(select(func.count(RegraExame.id)))
            total_incomp = await session.scalar(
                select(func.count(IncompatibilidadeExame.id))
            )
            assert total_prio == len(REGRAS_PRIORIDADE_INICIAIS)
            assert total_exames == len(REGRAS_EXAMES_INICIAIS)
            assert total_incomp == len(INCOMPATIBILIDADES_EXAMES_INICIAIS)

            # Garante ausência de duplicidades de chaves/pares
            codigos_prio = list(
                (await session.scalars(select(RegraPrioridade.codigo))).all()
            )
            assert len(codigos_prio) == len(set(codigos_prio))

            codigos_exames = list(
                (await session.scalars(select(RegraExame.codigo_exame))).all()
            )
            assert len(codigos_exames) == len(set(codigos_exames))

            pares_incomp = (
                await session.execute(
                    select(
                        IncompatibilidadeExame.codigo_exame_origem,
                        IncompatibilidadeExame.codigo_exame_conflitante,
                    )
                )
            ).all()
            assert len(pares_incomp) == len(set(pares_incomp))

            # Simula edição gerencial e soft delete para validar preservação
            onco = await session.scalar(
                select(RegraPrioridade).where(
                    RegraPrioridade.codigo == "CLINICA_ONCOLOGIA"
                )
            )
            assert onco is not None
            onco.peso = 120

            rotina = await session.scalar(
                select(RegraPrioridade).where(RegraPrioridade.codigo == "GRUPO_ROTINA")
            )
            assert rotina is not None
            rotina.deleted_at = datetime.now(timezone.utc)
            await session.commit()

        # 3ª execução: preserva edição (peso=120) e soft delete sem duplicar
        async with session_factory() as session:
            terceira = await seed_regras_iniciais(session)
            assert terceira == {
                "regras_prioridade": 0,
                "regras_exames": 0,
                "incompatibilidades_exames": 0,
            }

            onco_apos = await session.scalar(
                select(RegraPrioridade).where(
                    RegraPrioridade.codigo == "CLINICA_ONCOLOGIA"
                )
            )
            assert onco_apos is not None
            assert onco_apos.peso == 120

            rotina_apos = await session.scalar(
                select(RegraPrioridade).where(RegraPrioridade.codigo == "GRUPO_ROTINA")
            )
            assert rotina_apos is not None
            assert rotina_apos.deleted_at is not None

            assert (
                await session.scalar(select(func.count(RegraPrioridade.id)))
                == len(REGRAS_PRIORIDADE_INICIAIS)
            )
    finally:
        await async_engine.dispose()


@pytest.mark.asyncio
async def test_executar_seed_cli_idempotente_em_tmp_path(tmp_path: Path) -> None:
    """Valida que ``executar_seed_cli`` funciona de forma idempotente em DSN isolado."""
    db_path = tmp_path / "seed_cli.db"
    dsn = f"sqlite+aiosqlite:///{db_path}"

    primeira = await executar_seed_cli(dsn=dsn)
    assert primeira == {
        "regras_prioridade": len(REGRAS_PRIORIDADE_INICIAIS),
        "regras_exames": len(REGRAS_EXAMES_INICIAIS),
        "incompatibilidades_exames": len(INCOMPATIBILIDADES_EXAMES_INICIAIS),
    }

    segunda = await executar_seed_cli(dsn=dsn)
    assert segunda == {
        "regras_prioridade": 0,
        "regras_exames": 0,
        "incompatibilidades_exames": 0,
    }
