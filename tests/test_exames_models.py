"""
Suíte de Testes dos Modelos SQLAlchemy de Gestão de Fila de Exames
==================================================================
Valida registro em ``Base.metadata``, criação de schema em SQLite em memória
(síncrono e assíncrono), persistência CRUD, valores padrão, chaves estrangeiras,
restrições de integridade (CHECK/UNIQUE) e exclusão lógica (``deleted_at``)
para os 5 novos modelos de domínio definidos em ``docs/especificacao/04-modelo-dados.md``.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Generator

import pytest
from sqlalchemy import create_engine, delete, event, inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

import src.models as models_pkg
from src.models import (
    AcompanhamentoFila,
    AuditLog,
    ImportacaoForms,
    IncompatibilidadeExame,
    RefreshToken,
    RegraExame,
    RegraPrioridade,
)
from src.resources.database import Base


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    """Ativa a verificação de chaves estrangeiras no SQLite em cada conexão."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
def sqlite_engine() -> Generator[Engine, None, None]:
    """Cria um engine SQLite em memória com FK enforcement e schema completo."""
    engine = create_engine("sqlite:///:memory:", future=True)
    event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def db_session(sqlite_engine: Engine) -> Generator[Session, None, None]:
    """Fornece uma sessão SQLAlchemy isolada sobre o SQLite em memória."""
    session_factory = sessionmaker(
        bind=sqlite_engine,
        expire_on_commit=False,
        future=True,
    )
    with session_factory() as session:
        yield session


def test_exports_e_registro_no_base_metadata() -> None:
    """Valida exportações em src.models e o registro completo em Base.metadata."""
    expected_exports = {
        "AuditLog",
        "RefreshToken",
        "ImportacaoForms",
        "AcompanhamentoFila",
        "RegraPrioridade",
        "RegraExame",
        "IncompatibilidadeExame",
    }
    assert expected_exports.issubset(set(models_pkg.__all__))

    for model_cls in (
        AuditLog,
        RefreshToken,
        ImportacaoForms,
        AcompanhamentoFila,
        RegraPrioridade,
        RegraExame,
        IncompatibilidadeExame,
    ):
        assert issubclass(model_cls, Base)

    registered_tables = set(Base.metadata.tables.keys())
    expected_new_tables = {
        "importacoes_forms",
        "acompanhamento_fila",
        "regras_prioridade",
        "regras_exames",
        "incompatibilidades_exames",
    }
    assert expected_new_tables.issubset(registered_tables)

    assert set(Base.metadata.tables["importacoes_forms"].columns.keys()) == {
        "id",
        "nome_arquivo",
        "importado_em",
        "usuario_importador",
        "total_linhas",
        "total_validas",
        "total_duplicadas",
        "total_erros",
        "deleted_at",
    }

    assert set(Base.metadata.tables["acompanhamento_fila"].columns.keys()) == {
        "id",
        "importacao_id",
        "codigo_solicitacao",
        "codigo_exame",
        "prontuario",
        "nome_paciente",
        "telefone_contato",
        "municipio",
        "regiao_geografica",
        "utiliza_tfd",
        "data_retorno_medico",
        "exame_informado_forms",
        "unidade_solicitante",
        "especialidade_solicitante",
        "flag_hemodialise",
        "flag_diabetico_jejum",
        "grupo_prioritario_manual",
        "status_higienizacao",
        "status_operacional",
        "contato_iniciado_em",
        "prazo_confirmacao_em",
        "data_agendada_aghu",
        "preparo_orientado",
        "observacoes",
        "created_at",
        "updated_at",
        "deleted_at",
    }

    assert set(Base.metadata.tables["regras_prioridade"].columns.keys()) == {
        "id",
        "codigo",
        "nome",
        "tipo_criterio",
        "valor_match",
        "peso",
        "ativo",
        "descricao",
        "updated_at",
        "deleted_at",
    }

    assert set(Base.metadata.tables["regras_exames"].columns.keys()) == {
        "id",
        "codigo_exame",
        "nome_exame",
        "unidade_executora",
        "antecedencia_minima_dias",
        "janela_retorno_max_horas",
        "exige_jejum",
        "priorizar_manha_diabetico",
        "idade_minima_alerta",
        "orientacoes_preparo",
        "ativo",
        "updated_at",
        "deleted_at",
    }

    assert set(Base.metadata.tables["incompatibilidades_exames"].columns.keys()) == {
        "id",
        "codigo_exame_origem",
        "codigo_exame_conflitante",
        "tipo_conflito",
        "intervalo_minimo_dias",
        "motivo",
        "ativo",
        "deleted_at",
    }


def test_sqlite_in_memory_schema_creation_e_indices(sqlite_engine: Engine) -> None:
    """Valida criação física das tabelas, índices compostos e FKs no SQLite em memória."""
    inspector = inspect(sqlite_engine)
    table_names = set(inspector.get_table_names())

    for table in (
        "importacoes_forms",
        "acompanhamento_fila",
        "regras_prioridade",
        "regras_exames",
        "incompatibilidades_exames",
    ):
        assert table in table_names

    fila_indexes = {idx["name"] for idx in inspector.get_indexes("acompanhamento_fila")}
    assert {
        "ix_acompanhamento_fila_prontuario_exame",
        "ix_acompanhamento_fila_solicitacao_exame",
        "ix_acompanhamento_fila_status_ativos",
    }.issubset(fila_indexes)

    incompat_indexes = {
        idx["name"] for idx in inspector.get_indexes("incompatibilidades_exames")
    }
    assert "ix_incompatibilidades_exames_par" in incompat_indexes

    fila_fks = inspector.get_foreign_keys("acompanhamento_fila")
    assert any(
        fk["constrained_columns"] == ["importacao_id"]
        and fk["referred_table"] == "importacoes_forms"
        and fk["referred_columns"] == ["id"]
        for fk in fila_fks
    )

    incompat_fks = inspector.get_foreign_keys("incompatibilidades_exames")
    assert any(
        fk["constrained_columns"] == ["codigo_exame_origem"]
        and fk["referred_table"] == "regras_exames"
        and fk["referred_columns"] == ["codigo_exame"]
        for fk in incompat_fks
    )


def test_importacao_forms_crud_defaults_e_constraints(db_session: Session) -> None:
    """Valida CRUD, defaults e CHECK constraints em ImportacaoForms."""
    importacao = ImportacaoForms(
        nome_arquivo="forms_marco_2026.csv",
        usuario_importador="maria.central",
    )
    db_session.add(importacao)
    db_session.commit()
    db_session.refresh(importacao)

    assert importacao.id is not None
    assert importacao.total_linhas == 0
    assert importacao.total_validas == 0
    assert importacao.total_duplicadas == 0
    assert importacao.total_erros == 0
    assert importacao.importado_em is not None
    assert importacao.deleted_at is None
    assert importacao.is_deleted is False
    assert "ImportacaoForms" in repr(importacao)

    importacao.total_linhas = 50
    importacao.total_validas = 42
    importacao.total_duplicadas = 5
    importacao.total_erros = 3
    db_session.commit()

    fetched = db_session.get(ImportacaoForms, importacao.id)
    assert fetched is not None
    assert (
        fetched.total_linhas,
        fetched.total_validas,
        fetched.total_duplicadas,
        fetched.total_erros,
    ) == (50, 42, 5, 3)

    invalida = ImportacaoForms(
        nome_arquivo="erro_negativo.csv",
        usuario_importador="maria.central",
        total_linhas=-1,
    )
    db_session.add(invalida)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_acompanhamento_fila_crud_defaults_fk_e_constraints(
    db_session: Session,
) -> None:
    """Valida CRUD, defaults, FK/relacionamento e CHECK constraints em AcompanhamentoFila."""
    importacao = ImportacaoForms(
        nome_arquivo="lote_fila.xlsx",
        usuario_importador="joao.recepcao",
        total_linhas=2,
        total_validas=2,
    )
    db_session.add(importacao)
    db_session.commit()
    db_session.refresh(importacao)

    item_default = AcompanhamentoFila(
        importacao_id=importacao.id,
        codigo_solicitacao="890001",
        nome_paciente="PACIENTE ANONIMIZADO 01",
    )
    db_session.add(item_default)
    db_session.commit()
    db_session.refresh(item_default)

    assert item_default.id is not None
    assert item_default.prontuario is None
    assert item_default.codigo_exame is None
    assert item_default.regiao_geografica == "NAO_INFORMADO"
    assert item_default.utiliza_tfd is False
    assert item_default.flag_hemodialise is False
    assert item_default.flag_diabetico_jejum is False
    assert item_default.status_higienizacao == "VALIDA"
    assert item_default.status_operacional == "NA_FILA"
    assert item_default.preparo_orientado is False
    assert item_default.created_at is not None
    assert item_default.updated_at is not None
    assert item_default.deleted_at is None
    assert item_default.is_deleted is False
    assert item_default.importacao is not None
    assert item_default.importacao.id == importacao.id
    assert len(importacao.acompanhamentos) == 1
    assert "AcompanhamentoFila" in repr(item_default)

    # Atualização operacional com transição para AGUARDANDO_CONFIRMACAO_24H
    contato_em = datetime(2026, 3, 10, 14, 0, tzinfo=timezone.utc)
    prazo_em = contato_em + timedelta(hours=24)
    item_default.prontuario = "1194567"
    item_default.codigo_exame = "RXMM1"
    item_default.municipio = "Caruaru"
    item_default.regiao_geografica = "INTERIOR"
    item_default.utiliza_tfd = True
    item_default.data_retorno_medico = date(2026, 3, 25)
    item_default.status_operacional = "AGUARDANDO_CONFIRMACAO_24H"
    item_default.contato_iniciado_em = contato_em
    item_default.prazo_confirmacao_em = prazo_em
    item_default.preparo_orientado = True
    item_default.observacoes = "Contato via WhatsApp realizado."
    db_session.commit()

    fetched = db_session.get(AcompanhamentoFila, item_default.id)
    assert fetched is not None
    assert fetched.regiao_geografica == "INTERIOR"
    assert fetched.utiliza_tfd is True
    assert fetched.data_retorno_medico == date(2026, 3, 25)
    assert fetched.status_operacional == "AGUARDANDO_CONFIRMACAO_24H"
    assert fetched.preparo_orientado is True

    # Item avulso com importacao_id nulo (nullable=True)
    item_avulso = AcompanhamentoFila(
        importacao_id=None,
        codigo_solicitacao="890016",
        codigo_exame="USAX",
        prontuario=None,
        nome_paciente="PACIENTE SEM PRONTUARIO",
    )
    db_session.add(item_avulso)
    db_session.commit()
    assert item_avulso.id is not None
    assert item_avulso.importacao_id is None

    # FK inválida deve falhar
    item_fk_invalida = AcompanhamentoFila(
        importacao_id=999999,
        codigo_solicitacao="890999",
        nome_paciente="PACIENTE FK INVALIDA",
    )
    db_session.add(item_fk_invalida)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # ON DELETE RESTRICT impede exclusão física de ImportacaoForms com filhos
    with pytest.raises(IntegrityError):
        db_session.execute(
            delete(ImportacaoForms).where(ImportacaoForms.id == importacao.id)
        )
        db_session.commit()
    db_session.rollback()

    # CHECK constraints de domínio
    for invalid_kwargs in (
        {"regiao_geografica": "ZONA_INVALIDA"},
        {"status_higienizacao": "DESCONHECIDO"},
        {"status_operacional": "EXPIRADO"},
    ):
        invalido = AcompanhamentoFila(
            codigo_solicitacao="890777",
            nome_paciente="PACIENTE CHECK",
            **invalid_kwargs,
        )
        db_session.add(invalido)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


def test_regra_prioridade_crud_defaults_unique_e_constraints(
    db_session: Session,
) -> None:
    """Valida CRUD, defaults, unicidade e CHECK constraints em RegraPrioridade."""
    regra = RegraPrioridade(
        codigo="CLINICA_ONCOLOGIA",
        nome="Oncologia",
        tipo_criterio="CLINICA",
    )
    db_session.add(regra)
    db_session.commit()
    db_session.refresh(regra)

    assert regra.id is not None
    assert regra.valor_match == ""
    assert regra.peso == 0
    assert regra.ativo is True
    assert regra.descricao is None
    assert regra.updated_at is not None
    assert regra.deleted_at is None
    assert regra.is_deleted is False
    assert "RegraPrioridade" in repr(regra)

    regra.valor_match = "ONCOLOGIA"
    regra.peso = 100
    regra.descricao = "Prioridade máxima para solicitações da Oncologia."
    db_session.commit()

    fetched = db_session.get(RegraPrioridade, regra.id)
    assert fetched is not None
    assert fetched.peso == 100
    assert fetched.valor_match == "ONCOLOGIA"

    # Unicidade em codigo
    duplicada = RegraPrioridade(
        codigo="CLINICA_ONCOLOGIA",
        nome="Oncologia Duplicada",
        tipo_criterio="CLINICA",
        peso=80,
    )
    db_session.add(duplicada)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # CHECK em tipo_criterio e faixa de peso (0..1000)
    for bad_regra in (
        RegraPrioridade(
            codigo="CRITERIO_BAD",
            nome="Critério Inválido",
            tipo_criterio="NAO_EXISTE",
            peso=10,
        ),
        RegraPrioridade(
            codigo="PESO_NEGATIVO",
            nome="Peso Negativo",
            tipo_criterio="VULNERAVEL",
            peso=-1,
        ),
        RegraPrioridade(
            codigo="PESO_ACIMA",
            nome="Peso Acima",
            tipo_criterio="VULNERAVEL",
            peso=1001,
        ),
    ):
        db_session.add(bad_regra)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


def test_regra_exame_crud_defaults_unique_e_constraints(db_session: Session) -> None:
    """Valida CRUD, defaults, unicidade e CHECK constraints em RegraExame."""
    regra = RegraExame(
        codigo_exame="ESPIRO",
        nome_exame="ESPIROMETRIA COMPLETA",
    )
    db_session.add(regra)
    db_session.commit()
    db_session.refresh(regra)

    assert regra.id is not None
    assert regra.unidade_executora is None
    assert regra.antecedencia_minima_dias == 0
    assert regra.janela_retorno_max_horas is None
    assert regra.exige_jejum is False
    assert regra.priorizar_manha_diabetico is False
    assert regra.idade_minima_alerta is None
    assert regra.orientacoes_preparo is None
    assert regra.ativo is True
    assert regra.updated_at is not None
    assert regra.deleted_at is None
    assert regra.is_deleted is False
    assert "RegraExame" in repr(regra)

    regra.unidade_executora = "PNEUMOLOGIA"
    regra.antecedencia_minima_dias = 2
    regra.janela_retorno_max_horas = 240
    regra.orientacoes_preparo = "Suspender broncodilatador conforme orientação médica."
    db_session.commit()

    fetched = db_session.get(RegraExame, regra.id)
    assert fetched is not None
    assert fetched.janela_retorno_max_horas == 240
    assert fetched.antecedencia_minima_dias == 2

    # Unicidade em codigo_exame
    duplicada = RegraExame(
        codigo_exame="ESPIRO",
        nome_exame="ESPIROMETRIA DUPLICADA",
    )
    db_session.add(duplicada)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # CHECK constraints (>= 0)
    for bad_regra in (
        RegraExame(
            codigo_exame="BAD_ANT",
            nome_exame="Antecedencia Negativa",
            antecedencia_minima_dias=-1,
        ),
        RegraExame(
            codigo_exame="BAD_JAN",
            nome_exame="Janela Negativa",
            janela_retorno_max_horas=-10,
        ),
        RegraExame(
            codigo_exame="BAD_IDA",
            nome_exame="Idade Negativa",
            idade_minima_alerta=-5,
        ),
    ):
        db_session.add(bad_regra)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


def test_incompatibilidade_exame_crud_defaults_fk_e_constraints(
    db_session: Session,
) -> None:
    """Valida CRUD, defaults, FK/relacionamento e CHECK constraints em IncompatibilidadeExame."""
    regra_origem = RegraExame(
        codigo_exame="COLONO",
        nome_exame="COLONOSCOPIA",
        exige_jejum=True,
        priorizar_manha_diabetico=True,
    )
    db_session.add(regra_origem)
    db_session.commit()

    incompat = IncompatibilidadeExame(
        codigo_exame_origem="COLONO",
        codigo_exame_conflitante="HEMO",
        tipo_conflito="PREPARO",
        motivo="Preparo intestinal incompatível com sessão de hemodiálise no mesmo dia.",
    )
    db_session.add(incompat)
    db_session.commit()
    db_session.refresh(incompat)

    assert incompat.id is not None
    assert incompat.intervalo_minimo_dias == 0
    assert incompat.ativo is True
    assert incompat.deleted_at is None
    assert incompat.is_deleted is False
    assert incompat.regra_exame_origem is not None
    assert incompat.regra_exame_origem.codigo_exame == "COLONO"
    assert len(regra_origem.incompatibilidades) == 1
    assert "IncompatibilidadeExame" in repr(incompat)

    incompat.tipo_conflito = "INTERVALO_MINIMO"
    incompat.intervalo_minimo_dias = 2
    db_session.commit()

    fetched = db_session.get(IncompatibilidadeExame, incompat.id)
    assert fetched is not None
    assert fetched.tipo_conflito == "INTERVALO_MINIMO"
    assert fetched.intervalo_minimo_dias == 2

    # FK inválida (codigo_exame_origem inexistente em regras_exames)
    incompat_fk_invalida = IncompatibilidadeExame(
        codigo_exame_origem="INEXISTENTE",
        codigo_exame_conflitante="USAX",
        tipo_conflito="MESMO_DIA",
        motivo="Origem não cadastrada.",
    )
    db_session.add(incompat_fk_invalida)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # ON DELETE RESTRICT impede exclusão física de RegraExame referenciada
    with pytest.raises(IntegrityError):
        db_session.execute(
            delete(RegraExame).where(RegraExame.codigo_exame == "COLONO")
        )
        db_session.commit()
    db_session.rollback()

    # CHECK constraints de tipo_conflito e intervalo_minimo_dias
    for bad_incompat in (
        IncompatibilidadeExame(
            codigo_exame_origem="COLONO",
            codigo_exame_conflitante="USAX",
            tipo_conflito="CONFLITO_INVALIDO",
            motivo="Tipo inválido.",
        ),
        IncompatibilidadeExame(
            codigo_exame_origem="COLONO",
            codigo_exame_conflitante="USAX",
            tipo_conflito="INTERVALO_MINIMO",
            intervalo_minimo_dias=-2,
            motivo="Intervalo negativo.",
        ),
    ):
        db_session.add(bad_incompat)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


def test_soft_delete_todos_os_cinco_modelos(db_session: Session) -> None:
    """Valida exclusão lógica (deleted_at) sem remoção física nos 5 modelos."""
    importacao = ImportacaoForms(
        nome_arquivo="soft_delete.csv",
        usuario_importador="auditor.hc",
    )
    regra_prioridade = RegraPrioridade(
        codigo="GRUPO_TRANSPLANTE",
        nome="Transplante",
        tipo_criterio="GRUPO_CLINICO",
        valor_match="TRANSPLANTE",
        peso=80,
    )
    regra_exame = RegraExame(
        codigo_exame="RXMM1",
        nome_exame="MAMOGRAFIA BILATERAL",
        idade_minima_alerta=40,
    )
    db_session.add_all([importacao, regra_prioridade, regra_exame])
    db_session.commit()

    acompanhamento = AcompanhamentoFila(
        importacao_id=importacao.id,
        codigo_solicitacao="890005",
        codigo_exame="RXMM1",
        prontuario="1194567",
        nome_paciente="PACIENTE SOFT DELETE",
    )
    incompatibilidade = IncompatibilidadeExame(
        codigo_exame_origem="RXMM1",
        codigo_exame_conflitante="RMCRAN",
        tipo_conflito="MESMO_DIA",
        motivo="Evitar agenda simultânea de exames de imagem distintos.",
    )
    db_session.add_all([acompanhamento, incompatibilidade])
    db_session.commit()

    registros = [
        (ImportacaoForms, importacao),
        (AcompanhamentoFila, acompanhamento),
        (RegraPrioridade, regra_prioridade),
        (RegraExame, regra_exame),
        (IncompatibilidadeExame, incompatibilidade),
    ]

    for model_cls, obj in registros:
        assert obj.deleted_at is None
        assert obj.is_deleted is False

        obj.soft_delete()
        db_session.commit()
        db_session.refresh(obj)

        assert obj.deleted_at is not None
        assert obj.is_deleted is True

        # Registro permanece fisicamente no banco (proibição de hard delete)
        all_rows = db_session.scalars(select(model_cls)).all()
        assert len(all_rows) == 1
        assert all_rows[0].id == obj.id

        # Consulta de ativos (deleted_at IS NULL) não retorna o registro excluído
        active_rows = db_session.scalars(
            select(model_cls).where(model_cls.deleted_at.is_(None))
        ).all()
        assert active_rows == []


@pytest.mark.asyncio
async def test_sqlite_in_memory_async_schema_e_persistencia() -> None:
    """Valida criação de schema e persistência assíncrona com aiosqlite (stack real do app)."""
    async_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    event.listen(async_engine.sync_engine, "connect", _enable_sqlite_foreign_keys)

    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session_factory = async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session_factory() as session:
            pragma = (await session.execute(text("PRAGMA foreign_keys"))).scalar_one()
            assert pragma == 1

            importacao = ImportacaoForms(
                nome_arquivo="async_forms.csv",
                usuario_importador="operador.async",
                total_linhas=1,
                total_validas=1,
            )
            regra_prioridade = RegraPrioridade(
                codigo="RETORNO_15D",
                nome="Retorno em até 15 dias",
                tipo_criterio="RETORNO_PROXIMO",
                valor_match="<=15",
                peso=20,
            )
            regra_exame = RegraExame(
                codigo_exame="INR",
                nome_exame="TEMPO DE PROTROMBINA (INR)",
                janela_retorno_max_horas=72,
            )
            session.add_all([importacao, regra_prioridade, regra_exame])
            await session.flush()

            item_fila = AcompanhamentoFila(
                importacao_id=importacao.id,
                codigo_solicitacao="890010",
                codigo_exame="INR",
                prontuario="554433",
                nome_paciente="PACIENTE ASYNC",
                regiao_geografica="CAPITAL",
            )
            incompat = IncompatibilidadeExame(
                codigo_exame_origem="INR",
                codigo_exame_conflitante="COLONO",
                tipo_conflito="MESMO_DIA",
                motivo="Restrição de teste assíncrono.",
            )
            session.add_all([item_fila, incompat])
            await session.commit()

            assert (
                len((await session.scalars(select(ImportacaoForms))).all()) == 1
            )
            assert (
                len((await session.scalars(select(AcompanhamentoFila))).all()) == 1
            )
            assert (
                len((await session.scalars(select(RegraPrioridade))).all()) == 1
            )
            assert len((await session.scalars(select(RegraExame))).all()) == 1
            assert (
                len((await session.scalars(select(IncompatibilidadeExame))).all())
                == 1
            )
    finally:
        await async_engine.dispose()
