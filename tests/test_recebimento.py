# tests/test_recebimento.py
"""
Testes do recebimento e da conferência de amostras (RF003 a RF006).

Usam somente data/solicitacoes_aghu_exemplo.csv, com dados inventados no layout da view real.
"""
import asyncio
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import pytest_asyncio
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select, update

from src.auth.auth import auth_handler
from src.controllers import recebimento_controller
from src.dependencies import _get_solicitacao_csv_provider
from src.helpers.etiqueta_helper import interpretar_codigo_lido
from src.main import app
from src.models.audit_log import AuditLog
from src.models.exame import (
    Amostra,
    BANCADAS_INICIAIS,
    BancadaLaboratorio,
    ConferenciaAmostra,
    Exame,
    MOTIVOS_INICIAIS,
    NaoConformidade,
    PROCEDIMENTOS_HP_INICIAIS,
    SequenciaNumeroInterno,
    StatusItemAghu,
)
from src.providers.implementations.solicitacao_csv_provider import SolicitacaoCsvProvider
from src.providers.implementations.solicitacao_mapeamento import (
    COLUNAS_VIEW,
    converter_data,
    limpar_texto,
    limpar_texto_com_linhas,
    montar_solicitacao,
)
from src.providers.implementations.solicitacao_postgres_provider import SolicitacaoPostgresProvider
from src.providers.interfaces.solicitacao_provider_interface import SolicitacaoProviderInterface
from src.resources.database import Base, DatabaseManager, get_app_db_session

pytestmark = pytest.mark.asyncio

USUARIO = "recepcao.teste"
URL = "/api/recebimento/solicitacoes"
CSV_EXEMPLO = Path(__file__).parent.parent / "data" / "solicitacoes_aghu_exemplo.csv"

CODIGO_6_DIGITOS = "100123"
SO_HP = "9000101"
HP_TRES_AMOSTRAS = "9000102"
CG_LIQUIDO = "9000103"
CCV = "9000104"
CO = "9000105"
IHQ = "9000106"
CITO_SEM_DESCRICAO = "9000107"
CO_E_HP = "9000108"
TRES_BANCADAS = "9000109"
STATUS_MISTOS = "9000110"
EXTERNO_SEM_PRONTUARIO = "9000111"
EXTERNO_COM_PRONTUARIO = "9000112"
COM_LACUNAS = "9000113"
DUAS_SIGLAS_NO_HP = "9000114"
SEM_PRONTUARIO_FORA_DE_EXTERNO = "9000123"
SOLICITACAO_POR_STATUS = {
    "AC": "9000115",
    "EC": "9000116",
    "CO": "9000117",
    "AE": "9000118",
    "PE": "9000119",
    "EX": "9000120",
    "LI": "9000121",
    "CA": "9000122",
}

DADOS_HP = {"quantidade_pecas": 2, "urgente": False, "procedimento_id": 5}
TEXTO_CLINICO_DO_EXEMPLO = "Texto clínico fictício"
CHECKLIST = {"sigla_confere": True, "descricao_confere": True, "recipientes_confere": True}


def amostra(numero: int, receber: bool = True, **extras: Any) -> Dict[str, Any]:
    """Monta a marcação de uma amostra."""
    return {"numero_amostra": numero, "receber": receber, **extras}


@pytest.fixture(autouse=True)
def csv_de_exemplo(monkeypatch):
    """Garante que os testes nunca usem outro CSV, mesmo com o .env apontando para o real."""
    monkeypatch.setenv("SOLICITACAO_CSV_PATH", str(CSV_EXEMPLO))


@pytest_asyncio.fixture
async def banco(tmp_path):
    """Cria um banco SQLite em arquivo temporário e o usa no lugar de data/app.db."""
    gerenciador = DatabaseManager(f"sqlite+aiosqlite:///{tmp_path / 'teste.db'}")
    async with gerenciador.engine.begin() as conexao:
        await conexao.run_sync(Base.metadata.create_all)

    async def sessao_de_teste():
        """Fornece uma sessão do banco temporário."""
        async for sessao in gerenciador.get_session():
            yield sessao

    app.dependency_overrides[get_app_db_session] = sessao_de_teste
    yield gerenciador
    app.dependency_overrides.pop(get_app_db_session, None)
    await gerenciador.close_connection()


@pytest_asyncio.fixture
async def anonimo(banco):
    """Cliente HTTP sem token."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://teste") as cliente:
        yield cliente


@pytest_asyncio.fixture
async def api(banco):
    """Cliente HTTP autenticado."""
    token = auth_handler.create_access_token({"username": USUARIO, "groups": []})
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://teste",
        headers={"Authorization": f"Bearer {token}"},
    ) as cliente:
        yield cliente


async def consultar(banco: DatabaseManager, consulta: Any) -> List[Any]:
    """Executa uma consulta no banco temporário e retorna os objetos encontrados."""
    async with banco.async_session_maker() as sessao:
        return list((await sessao.execute(consulta)).scalars())


async def primeiro_motivo(api: AsyncClient) -> int:
    """Retorna o id do primeiro motivo de não conformidade."""
    resposta = await api.get("/api/recebimento/motivos-nao-conformidade")
    return resposta.json()[0]["id"]


async def devolver(api: AsyncClient, codigo: str, **extras: Any) -> Any:
    """Registra uma não conformidade com o primeiro motivo da lista."""
    motivo = await primeiro_motivo(api)
    return await api.post(
        f"{URL}/{codigo}/nao-conformidades",
        json={"motivo_id": motivo, "observacao": "Frasco sem etiqueta.", **extras},
    )


async def receber(api: AsyncClient, codigo: str, *numeros: int, **extras: Any) -> Any:
    """Recebe as amostras informadas com o checklist completo e os dados de HP preenchidos."""
    corpo = {**CHECKLIST, "amostras": [amostra(numero) for numero in numeros], "dados_hp": DADOS_HP, **extras}
    return await api.post(f"{URL}/{codigo}/recebimentos", json=corpo)


class ProviderFixo(SolicitacaoProviderInterface):
    """Retorna uma solicitação montada pelo teste, para casos que não existem no CSV real."""

    def __init__(self, itens: List[Dict[str, Any]]) -> None:
        """Guarda as amostras da solicitação."""
        self.itens = itens

    async def obter_solicitacao_por_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
        """Retorna a solicitação com as amostras recebidas no construtor."""
        return {
            "codigo": codigo,
            "data_solicitacao": "2026-03-02",
            "nome_paciente": "C.A.R.",
            "data_nascimento": "1980-01-01",
            "prontuario": "99999999",
            "especialidade": "TESTE",
            "convenio": "SUS",
            "origem": "Ambulatório",
            "unidade": "TESTE",
            "informacoes_clinica": None,
            "itens": self.itens,
        }

    async def listar_solicitacoes(self, *_: Any) -> Dict[str, Any]:
        """Os testes com este provider não usam a lista."""
        return {"total": 0, "solicitacoes": []}


def item_fixo(codigo_lab: str = "207", cod_status: str = "CO", numero: int = 1) -> Dict[str, Any]:
    """Monta uma amostra para o ProviderFixo."""
    return {
        "numero_amostra": numero,
        "codigo_lab": codigo_lab,
        "sigla_exame": "APECR",
        "nome_exame": "ANATOMOPATOLÓGICO - PEÇA CIRÚRGICA",
        "descricao_material": "Fragmento",
        "cod_status_item": cod_status,
        "status_item_exame": "COLETADO",
    }


@pytest.fixture
def usar_provider_fixo():
    """Troca o provider de solicitações por um ProviderFixo com as amostras informadas."""

    def trocar(*itens: Dict[str, Any]) -> None:
        """Instala o provider com as amostras do teste."""
        app.dependency_overrides[_get_solicitacao_csv_provider] = lambda: ProviderFixo(list(itens))

    yield trocar
    app.dependency_overrides.pop(_get_solicitacao_csv_provider, None)


# --- Parser do código lido ---
@pytest.mark.parametrize(
    "lido,esperado",
    [
        ("9000101", ("9000101", None)),
        ("100123", ("100123", None)),
        (" 9000101 ", ("9000101", None)),
        ("9000101001", ("9000101", 1)),
        ("100123030", ("100123", 30)),
        ("9000101-1", ("9000101", 1)),
        ("9000101-30", ("9000101", 30)),
        ("100123-2", ("100123", 2)),
        ("9000101-001", ("9000101", 1)),
    ],
)
async def test_parser_aceita_os_formatos_da_etiqueta(lido, esperado):
    assert interpretar_codigo_lido(lido) == esperado


@pytest.mark.parametrize(
    "lido",
    [
        "",
        "abc",
        "12345",
        "99000101",  # 8 dígitos: ambíguo e igual ao tamanho do prontuário.
        "90001010011",
        "9000101000",  # Amostra zero.
        "9000101-0",
        "9000101-",
        "9000101-1234",
        "-1",
        "9000101.1",
    ],
)
async def test_parser_recusa_outros_formatos(lido):
    assert interpretar_codigo_lido(lido) is None


@pytest.mark.parametrize("formato", ["{}", "{}001", "{}-1"])
async def test_os_tres_formatos_abrem_a_solicitacao(api, formato):
    resposta = await api.get(f"{URL}/{formato.format(HP_TRES_AMOSTRAS)}")

    assert resposta.status_code == 200
    assert resposta.json()["codigo"] == HP_TRES_AMOSTRAS


async def test_codigo_de_6_digitos_abre_a_solicitacao(api):
    resposta = await api.get(f"{URL}/{CODIGO_6_DIGITOS}001")

    assert resposta.status_code == 200
    assert resposta.json()["codigo"] == CODIGO_6_DIGITOS


async def test_codigo_lido_invalido_retorna_422_com_detalhe(api):
    resposta = await api.get(f"{URL}/99000101")

    assert resposta.status_code == 422
    assert "inválido" in resposta.json()["detail"]


# --- Critério 1: bancada vem de codigo_lab, e só as bancadas configuradas são recebíveis ---
@pytest.mark.parametrize(
    "codigo,bancada,sigla",
    [
        (SO_HP, "HP", "APECR"),
        (CG_LIQUIDO, "CG", "CITOP"),
        (CCV, "CCV", "CCVM"),
        (CO, "CO", "CONGE"),
        (IHQ, "IHQ", "IMUHI"),
    ],
)
async def test_bancada_vem_do_codigo_lab_e_sigla_so_descreve_o_exame(api, codigo, bancada, sigla):
    resposta = await api.get(f"{URL}/{codigo}")

    assert resposta.status_code == 200
    item = resposta.json()["amostras"][0]
    assert item["bancada"] == bancada
    assert item["sigla_exame"] == sigla
    assert item["nome_exame"]


async def test_mapeamento_inicial_tem_as_5_bancadas(banco):
    linhas = await consultar(banco, select(BancadaLaboratorio))

    assert {(linha.codigo_lab, linha.bancada, linha.prefixo) for linha in linhas} == {
        ("207", "HP", "HP"),
        ("203", "CG", "CG"),
        ("139", "CCV", "CCV"),
        ("205", "CO", "CO"),
        ("209", "IHQ", "IH"),
    }
    assert len(BANCADAS_INICIAIS) == 5


async def test_laboratorio_inativo_deixa_de_ser_recebivel(api, banco):
    async with banco.async_session_maker() as sessao:
        await sessao.execute(
            update(BancadaLaboratorio)
            .where(BancadaLaboratorio.codigo_lab == "207")
            .values(ativo=False)
        )
        await sessao.commit()

    resposta = await api.get(f"{URL}/{SO_HP}")

    assert resposta.status_code == 422
    assert "Anatomia Patológica" in resposta.json()["detail"]


async def test_item_de_laboratorio_nao_mapeado_e_ignorado(api, usar_provider_fixo):
    usar_provider_fixo(item_fixo(), item_fixo(codigo_lab="999", numero=2))

    resposta = await api.get(f"{URL}/{SO_HP}")

    assert [item["numero_amostra"] for item in resposta.json()["amostras"]] == [1]


async def test_item_de_laboratorio_nao_mapeado_nao_pode_ser_recebido(api, usar_provider_fixo):
    usar_provider_fixo(item_fixo(), item_fixo(codigo_lab="999", numero=2))

    resposta = await receber(api, SO_HP, 2)

    assert resposta.status_code == 422
    assert "2" in resposta.json()["detail"]


async def test_solicitacao_so_de_laboratorio_nao_mapeado_retorna_422(api, usar_provider_fixo):
    usar_provider_fixo(item_fixo(codigo_lab="999"))

    resposta = await api.get(f"{URL}/{SO_HP}")

    assert resposta.status_code == 422


async def test_tela_recebe_os_dados_do_paciente_e_da_clinica(api):
    resposta = await api.get(f"{URL}/{SO_HP}")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados["paciente"]["nome"] == "Z.Y.X."
    assert dados["paciente"]["prontuario"] == "99000101"
    assert dados["paciente"]["data_nascimento"] == "1980-05-14"
    assert isinstance(dados["paciente"]["idade"], int)
    assert dados["data_solicitacao"] == "2026-03-02"
    assert dados["origem"] == "Internação"
    assert dados["especialidade"] == "CIRURGIA GERAL"
    assert dados["unidade"] == "9º SUL"
    assert dados["informacoes_clinica"].startswith(TEXTO_CLINICO_DO_EXEMPLO)


async def test_idade_e_calculada_com_a_data_do_aghu(api, monkeypatch):
    monkeypatch.setattr(
        recebimento_controller, "_agora", lambda: datetime(2026, 5, 14, 15, 0, tzinfo=timezone.utc)
    )

    resposta = await api.get(f"{URL}/{SO_HP}")

    assert resposta.json()["paciente"]["idade"] == 46


# --- Lista inicial paginada ---
async def test_lista_vem_paginada_da_mais_recente_para_a_mais_antiga(api):
    resposta = await api.get(f"{URL}?pagina=1&por_pagina=5")

    assert resposta.status_code == 200
    dados = resposta.json()
    assert (dados["pagina"], dados["por_pagina"]) == (1, 5)
    assert len(dados["solicitacoes"]) == 5
    assert dados["total_paginas"] == -(-dados["total"] // 5)
    datas = [item["data_solicitacao"] for item in dados["solicitacoes"]]
    assert datas == sorted(datas, reverse=True)
    assert dados["solicitacoes"][0]["codigo"] == SEM_PRONTUARIO_FORA_DE_EXTERNO


async def test_paginas_nao_repetem_solicitacoes(api):
    primeira = (await api.get(f"{URL}?pagina=1&por_pagina=4")).json()
    segunda = (await api.get(f"{URL}?pagina=2&por_pagina=4")).json()

    codigos_1 = {item["codigo"] for item in primeira["solicitacoes"]}
    codigos_2 = {item["codigo"] for item in segunda["solicitacoes"]}
    assert len(codigos_2) == 4
    assert not codigos_1 & codigos_2


async def test_pagina_alem_do_fim_vem_vazia(api):
    resposta = await api.get(f"{URL}?pagina=999")

    assert resposta.status_code == 200
    assert resposta.json()["solicitacoes"] == []
    assert resposta.json()["total"] > 0


@pytest.mark.parametrize(
    "consulta", ["pagina=0", "por_pagina=0", "por_pagina=101", "pagina=x", "somente_recebiveis=talvez"]
)
async def test_parametros_invalidos_da_lista_retornam_400(api, consulta):
    resposta = await api.get(f"{URL}?{consulta}")

    assert resposta.status_code == 400
    assert isinstance(resposta.json()["detail"], str)


async def test_filtro_padrao_esconde_solicitacoes_so_com_status_bloqueado(api):
    filtrada = (await api.get(f"{URL}?por_pagina=100")).json()
    completa = (await api.get(f"{URL}?por_pagina=100&somente_recebiveis=false")).json()

    codigos = {item["codigo"] for item in filtrada["solicitacoes"]}
    todos = {item["codigo"] for item in completa["solicitacoes"]}
    bloqueadas = {SOLICITACAO_POR_STATUS[status_item] for status_item in ("EX", "LI", "CA")}
    assert not codigos & bloqueadas
    assert bloqueadas <= todos
    assert STATUS_MISTOS in codigos
    assert completa["total"] == filtrada["total"] + 3


async def test_lista_nao_expoe_informacoes_clinicas(api):
    resposta = await api.get(f"{URL}?por_pagina=100")

    assert TEXTO_CLINICO_DO_EXEMPLO not in resposta.text


async def test_linha_da_lista_resume_a_solicitacao(api):
    dados = (await api.get(f"{URL}?por_pagina=100")).json()
    linha = next(item for item in dados["solicitacoes"] if item["codigo"] == CO_E_HP)

    assert linha["paciente"]["nome"] == "E.D.C."
    assert linha["paciente"]["prontuario"] == "99000108"
    assert isinstance(linha["paciente"]["idade"], int)
    assert linha["bancadas"] == ["CO", "HP"]
    assert (linha["total_amostras"], linha["amostras_recebiveis"]) == (2, 2)
    assert linha["numeros_internos"] == []
    assert linha["situacao"] == "AGUARDANDO"


async def linha_da_lista(api: AsyncClient, codigo: str) -> Dict[str, Any]:
    """Retorna a linha de uma solicitação na lista completa."""
    dados = (await api.get(f"{URL}?por_pagina=100&somente_recebiveis=false")).json()
    return next(item for item in dados["solicitacoes"] if item["codigo"] == codigo)


async def test_situacao_na_lista_acompanha_o_recebimento(api):
    assert (await linha_da_lista(api, CO_E_HP))["situacao"] == "AGUARDANDO"

    await receber(api, CO_E_HP, 1)
    parcial = await linha_da_lista(api, CO_E_HP)
    assert parcial["situacao"] == "PARCIAL"
    assert parcial["numeros_internos"] == ["CO 1"]
    assert parcial["amostras_recebiveis"] == 1

    await receber(api, CO_E_HP, 2)
    recebida = await linha_da_lista(api, CO_E_HP)
    assert recebida["situacao"] == "RECEBIDA"
    assert recebida["numeros_internos"] == ["CO 1", "HP 1"]
    assert recebida["amostras_recebiveis"] == 0


async def test_situacao_devolvida_e_bloqueada_na_lista(api):
    await devolver(api, SO_HP)

    assert (await linha_da_lista(api, SO_HP))["situacao"] == "DEVOLVIDA"
    assert (await linha_da_lista(api, SOLICITACAO_POR_STATUS["LI"]))["situacao"] == "BLOQUEADA"


async def test_laboratorio_inativo_sai_da_lista(api, banco):
    async with banco.async_session_maker() as sessao:
        await sessao.execute(
            update(BancadaLaboratorio)
            .where(BancadaLaboratorio.codigo_lab == "209")
            .values(ativo=False)
        )
        await sessao.commit()

    dados = (await api.get(f"{URL}?por_pagina=100&somente_recebiveis=false")).json()

    assert IHQ not in {item["codigo"] for item in dados["solicitacoes"]}


async def test_detalhe_traz_situacao_e_urgencia(api):
    aguardando = (await api.get(f"{URL}/{SO_HP}")).json()
    assert aguardando["situacao"] == "AGUARDANDO"
    assert aguardando["urgente"] is False

    com_co = (await api.get(f"{URL}/{CO_E_HP}")).json()
    assert com_co["urgente"] is True

    await receber(api, CO_E_HP, 1)
    parcial = (await api.get(f"{URL}/{CO_E_HP}")).json()
    assert parcial["situacao"] == "PARCIAL"

    await receber(api, SO_HP, 1, dados_hp={**DADOS_HP, "urgente": True})
    recebida = (await api.get(f"{URL}/{SO_HP}")).json()
    assert recebida["situacao"] == "RECEBIDA"
    assert recebida["urgente"] is True

    bloqueada = (await api.get(f"{URL}/{SOLICITACAO_POR_STATUS['LI']}")).json()
    assert bloqueada["situacao"] == "BLOQUEADA"


async def test_detalhe_mostra_o_que_foi_gravado_no_recebimento(api):
    await receber(
        api,
        HP_TRES_AMOSTRAS,
        1,
        2,
        dados_hp={"quantidade_pecas": 3, "urgente": True, "procedimento_id": 2},
    )

    dados = (await api.get(f"{URL}/{HP_TRES_AMOSTRAS}")).json()

    exame = dados["exames"][0]
    assert exame["quantidade_pecas"] == 3
    assert exame["urgente"] is True
    assert exame["procedimento"] == PROCEDIMENTOS_HP_INICIAIS[1]
    assert exame["nao_conformidades"] == []
    por_numero = {item["numero_amostra"]: item for item in dados["amostras"]}
    assert por_numero[1]["recebida"] is True
    assert por_numero[1]["conferencia"]["conferido_por"] == USUARIO
    assert por_numero[1]["conferencia"]["conferido_em"].endswith("Z")
    assert por_numero[3]["recebida"] is False
    assert por_numero[3]["conferencia"] is None


async def test_detalhe_mostra_material_informado_e_referencia_ao_hp(api):
    await api.post(
        f"{URL}/{CITO_SEM_DESCRICAO}/recebimentos",
        json={**CHECKLIST, "amostras": [amostra(1, descricao_informada="Lâmina fictícia")], "dados_hp": DADOS_HP},
    )
    await receber(api, IHQ, 1, referencia_hp="HP-2025/24")

    cito = (await api.get(f"{URL}/{CITO_SEM_DESCRICAO}")).json()
    assert cito["amostras"][0]["material_informado"] == "Lâmina fictícia"
    assert cito["exames"][0]["amostras"][0]["descricao_informada"] == "Lâmina fictícia"
    ihq = (await api.get(f"{URL}/{IHQ}")).json()
    assert ihq["exames"][0]["referencia_hp"] == "HP-2025/24"


async def test_detalhe_mostra_a_nao_conformidade_e_a_resolucao(api):
    await devolver(api, SO_HP, numero_cmce="12345", medico_solicitante="Médico Fictício")

    devolvida = (await api.get(f"{URL}/{SO_HP}")).json()
    assert devolvida["situacao"] == "DEVOLVIDA"
    registro = devolvida["exames"][0]["nao_conformidades"][0]
    assert registro["motivo"] == MOTIVOS_INICIAIS[0]
    assert registro["observacao"] == "Frasco sem etiqueta."
    assert registro["numero_cmce"] == "12345"
    assert registro["medico_solicitante"] == "Médico Fictício"
    assert registro["registrado_por"] == USUARIO
    assert registro["registrado_em"].endswith("Z")
    assert registro["resolvida"] is False
    assert registro["resolvida_em"] is None

    await receber(api, SO_HP, 1)

    recebida = (await api.get(f"{URL}/{SO_HP}")).json()
    registro = recebida["exames"][0]["nao_conformidades"][0]
    assert registro["resolvida"] is True
    assert registro["resolvida_por"] == USUARIO
    assert registro["resolvida_em"].endswith("Z")
    assert [exame["status"] for exame in recebida["exames"]] == ["DEVOLVIDO", "RECEBIDO"]


async def test_detalhe_traz_todas_as_colunas_do_aghu(api):
    dados = (await api.get(f"{URL}/{SO_HP}")).json()

    assert dados["convenio"] == "SUS"
    assert dados["amostras"][0]["codigo_lab"] == "207"
    assert dados["amostras"][0]["cod_status_item"] == "CO"


# --- Critério 2: código inexistente ---
async def test_codigo_inexistente_retorna_404_com_detalhe(api):
    resposta = await api.get(f"{URL}/9999999")

    assert resposta.status_code == 404
    assert "9999999" in resposta.json()["detail"]


async def test_etiqueta_com_amostra_destaca_a_amostra_lida(api):
    resposta = await api.get(f"{URL}/{HP_TRES_AMOSTRAS}002")

    assert resposta.status_code == 200
    assert resposta.json()["codigo"] == HP_TRES_AMOSTRAS
    assert resposta.json()["numero_amostra_lida"] == 2


async def test_etiqueta_com_amostra_desconhecida_retorna_404(api):
    resposta = await api.get(f"{URL}/{HP_TRES_AMOSTRAS}-9")

    assert resposta.status_code == 404


async def test_numeracao_com_lacunas_e_aceita(api, banco):
    consulta = await api.get(f"{URL}/{COM_LACUNAS}")
    assert [item["numero_amostra"] for item in consulta.json()["amostras"]] == [3, 5]

    resposta = await receber(api, COM_LACUNAS, 3, 5)

    assert resposta.status_code == 201
    amostras = await consultar(banco, select(Amostra).order_by(Amostra.numero_amostra))
    assert [item.numero_amostra for item in amostras] == [3, 5]


# --- Status do item no AGHU ---
@pytest.mark.parametrize("status_item", ["AC", "EC", "CO", "AE", "PE"])
async def test_status_que_permitem_recebimento(api, status_item):
    codigo = SOLICITACAO_POR_STATUS[status_item]

    consulta = await api.get(f"{URL}/{codigo}")
    assert consulta.json()["amostras"][0]["recebivel"] is True
    assert consulta.json()["amostras"][0]["cod_status_item"] == status_item

    resposta = await receber(api, codigo, 1)
    assert resposta.status_code == 201


@pytest.mark.parametrize(
    "status_item,nome", [("EX", "EXECUTANDO"), ("LI", "LIBERADO"), ("CA", "CANCELADO")]
)
async def test_status_que_bloqueiam_recebimento(api, banco, status_item, nome):
    codigo = SOLICITACAO_POR_STATUS[status_item]

    consulta = await api.get(f"{URL}/{codigo}")
    item = consulta.json()["amostras"][0]
    assert item["recebivel"] is False
    assert nome in item["motivo_bloqueio"]
    assert item["status_item_exame"] == nome

    resposta = await receber(api, codigo, 1)
    assert resposta.status_code == 422
    assert nome in resposta.json()["detail"]
    assert await consultar(banco, select(SequenciaNumeroInterno)) == []


@pytest.mark.parametrize("status_item", ["EX", "LI", "CA"])
async def test_nao_conformidade_vale_para_status_bloqueado(api, status_item):
    resposta = await devolver(api, SOLICITACAO_POR_STATUS[status_item])

    assert resposta.status_code == 201
    assert resposta.json()["exames"][0]["status"] == "DEVOLVIDO"


async def test_status_desconhecido_bloqueia_o_recebimento(api, usar_provider_fixo):
    usar_provider_fixo(item_fixo(cod_status="ZZ"))

    consulta = await api.get(f"{URL}/{SO_HP}")
    assert consulta.json()["amostras"][0]["recebivel"] is False
    assert "ZZ" in consulta.json()["amostras"][0]["motivo_bloqueio"]

    resposta = await receber(api, SO_HP, 1)
    assert resposta.status_code == 422


async def test_regra_de_status_vem_do_banco(api, banco):
    async with banco.async_session_maker() as sessao:
        await sessao.execute(
            update(StatusItemAghu)
            .where(StatusItemAghu.codigo == "EX")
            .values(permite_recebimento=True)
        )
        await sessao.commit()

    resposta = await receber(api, SOLICITACAO_POR_STATUS["EX"], 1)

    assert resposta.status_code == 201


async def test_status_mistos_bloqueiam_por_item(api, banco):
    consulta = await api.get(f"{URL}/{STATUS_MISTOS}")
    por_numero = {item["numero_amostra"]: item for item in consulta.json()["amostras"]}
    assert por_numero[1]["recebivel"] is False
    assert por_numero[2]["recebivel"] is True

    bloqueada = await receber(api, STATUS_MISTOS, 1, 2)
    assert bloqueada.status_code == 422

    resposta = await receber(api, STATUS_MISTOS, 2)
    assert resposta.status_code == 201
    amostras = await consultar(banco, select(Amostra).order_by(Amostra.numero_amostra))
    assert [(item.numero_amostra, item.recebida, item.cod_status_item) for item in amostras] == [
        (1, False, "LI"),
        (2, True, "AE"),
    ]


# --- Critério 3: checklist obrigatório ---
@pytest.mark.parametrize("item", ["sigla_confere", "descricao_confere", "recipientes_confere"])
async def test_checklist_incompleto_bloqueia_recebimento(api, banco, item):
    resposta = await api.post(
        f"{URL}/{SO_HP}/recebimentos",
        json={**CHECKLIST, item: False, "amostras": [amostra(1)], "dados_hp": DADOS_HP},
    )

    assert resposta.status_code == 422
    assert "checklist" in resposta.json()["detail"]
    assert await consultar(banco, select(Exame)) == []
    assert await consultar(banco, select(SequenciaNumeroInterno)) == []


async def test_recebimento_sem_checklist_e_bloqueado(api, banco):
    resposta = await api.post(
        f"{URL}/{SO_HP}/recebimentos", json={"amostras": [amostra(1)], "dados_hp": DADOS_HP}
    )

    assert resposta.status_code == 422
    assert "checklist" in resposta.json()["detail"]
    assert await consultar(banco, select(Exame)) == []


async def test_checklist_dentro_da_amostra_nao_vale(api, banco):
    resposta = await api.post(
        f"{URL}/{SO_HP}/recebimentos",
        json={"amostras": [amostra(1, sigla_confere=True, descricao_confere=True, recipientes_confere=True)], "dados_hp": DADOS_HP},
    )

    assert resposta.status_code == 422
    assert await consultar(banco, select(Exame)) == []


@pytest.mark.parametrize("valor", ["sim", 1, None])
async def test_checklist_so_aceita_verdadeiro_ou_falso(api, banco, valor):
    resposta = await api.post(
        f"{URL}/{SO_HP}/recebimentos",
        json={**CHECKLIST, "sigla_confere": valor, "amostras": [amostra(1)], "dados_hp": DADOS_HP},
    )

    assert resposta.status_code == 400
    assert await consultar(banco, select(Exame)) == []


async def test_checklist_unico_vale_para_todas_as_amostras_recebidas(api, banco):
    resposta = await receber(api, CO_E_HP, 1, 2)

    assert resposta.status_code == 201
    conferencias = await consultar(banco, select(ConferenciaAmostra))
    assert len(conferencias) == 2
    assert all(
        item.sigla_confere and item.descricao_confere and item.recipientes_confere
        for item in conferencias
    )
    assert {item.conferido_por for item in conferencias} == {USUARIO}


async def test_amostra_nao_marcada_nao_recebe_conferencia(api, banco):
    await receber(api, HP_TRES_AMOSTRAS, 1)

    assert len(await consultar(banco, select(ConferenciaAmostra))) == 1


async def test_checklist_completo_conclui_recebimento(api, banco):
    resposta = await receber(api, SO_HP, 1)

    assert resposta.status_code == 201
    exame = resposta.json()["exames"][0]
    assert exame["numero_interno"] == "HP 1"
    assert exame["status"] == "RECEBIDO"
    assert exame["recebido_por"] == USUARIO
    assert exame["recebido_em"].endswith("Z")
    conferencias = await consultar(banco, select(ConferenciaAmostra))
    assert len(conferencias) == 1
    assert conferencias[0].conferido_por == USUARIO
    assert conferencias[0].conferido_em is not None


async def test_recebimento_sem_amostra_marcada_e_bloqueado(api):
    resposta = await api.post(
        f"{URL}/{SO_HP}/recebimentos", json={**CHECKLIST, "amostras": [amostra(1, receber=False)]}
    )

    assert resposta.status_code == 422


async def test_corpo_invalido_retorna_400_com_detalhe_em_texto(api):
    resposta = await api.post(f"{URL}/{SO_HP}/recebimentos", json={**CHECKLIST, "amostras": []})

    assert resposta.status_code == 400
    assert isinstance(resposta.json()["detail"], str)


# --- Descrição vazia no AGHU (sigla CITO) ---
async def test_cito_sem_descricao_exige_material_informado(api, banco):
    consulta = await api.get(f"{URL}/{CITO_SEM_DESCRICAO}")
    item = consulta.json()["amostras"][0]
    assert item["sigla_exame"] == "CITO"
    assert item["descricao_material"] is None
    assert item["exige_descricao"] is True
    assert item["recebivel"] is True

    sem_material = await receber(api, CITO_SEM_DESCRICAO, 1)
    assert sem_material.status_code == 422
    assert "Informe o material" in sem_material.json()["detail"]

    so_espacos = await api.post(
        f"{URL}/{CITO_SEM_DESCRICAO}/recebimentos",
        json={**CHECKLIST, "amostras": [amostra(1, descricao_informada="   ")], "dados_hp": DADOS_HP},
    )
    assert so_espacos.status_code == 422
    assert await consultar(banco, select(SequenciaNumeroInterno)) == []


async def test_cito_com_material_informado_e_recebido(api, banco):
    resposta = await api.post(
        f"{URL}/{CITO_SEM_DESCRICAO}/recebimentos",
        json={**CHECKLIST, "amostras": [amostra(1, descricao_informada=" Lâmina fictícia ")], "dados_hp": DADOS_HP},
    )

    assert resposta.status_code == 201
    gravada = (await consultar(banco, select(Amostra)))[0]
    assert gravada.descricao_material is None
    assert gravada.descricao_informada == "Lâmina fictícia"


async def test_material_informado_nao_substitui_a_descricao_do_aghu(api, banco):
    resposta = await api.post(
        f"{URL}/{SO_HP}/recebimentos",
        json={**CHECKLIST, "amostras": [amostra(1, descricao_informada="Outro texto")], "dados_hp": DADOS_HP},
    )

    assert resposta.status_code == 201
    gravada = (await consultar(banco, select(Amostra)))[0]
    assert gravada.descricao_material == "Fragmento fictício de cólon"
    assert gravada.descricao_informada is None


async def test_nao_conformidade_de_amostra_sem_descricao_e_aceita(api):
    resposta = await devolver(api, CITO_SEM_DESCRICAO)

    assert resposta.status_code == 201


# --- Paciente Externo ---
async def test_paciente_externo_sem_prontuario_e_recebido(api, banco):
    consulta = await api.get(f"{URL}/{EXTERNO_SEM_PRONTUARIO}")
    dados = consulta.json()
    assert dados["paciente"]["prontuario"] is None
    assert dados["especialidade"] is None
    assert dados["amostras"][0]["recebivel"] is True

    resposta = await receber(api, EXTERNO_SEM_PRONTUARIO, 1)

    assert resposta.status_code == 201
    exame = (await consultar(banco, select(Exame)))[0]
    assert exame.prontuario is None
    assert exame.especialidade is None
    assert exame.origem == "Paciente Externo"


async def test_paciente_externo_com_prontuario_guarda_o_prontuario(api, banco):
    resposta = await receber(api, EXTERNO_COM_PRONTUARIO, 1)

    assert resposta.status_code == 201
    exame = (await consultar(banco, select(Exame)))[0]
    assert exame.prontuario == "99000112"
    assert exame.especialidade is None


async def test_sem_prontuario_fora_de_paciente_externo_bloqueia(api):
    consulta = await api.get(f"{URL}/{SEM_PRONTUARIO_FORA_DE_EXTERNO}")
    assert consulta.json()["amostras"][0]["recebivel"] is False
    assert "Prontuário" in consulta.json()["amostras"][0]["motivo_bloqueio"]

    resposta = await receber(api, SEM_PRONTUARIO_FORA_DE_EXTERNO, 1)
    assert resposta.status_code == 422


async def test_exame_guarda_clinica_e_unidade_do_aghu(api, banco):
    await receber(api, SO_HP, 1)

    exame = (await consultar(banco, select(Exame)))[0]
    assert exame.especialidade == "CIRURGIA GERAL"
    assert exame.unidade == "9º SUL"


# --- Dados que a recepção acrescenta ---
async def test_hp_exige_dados_complementares(api, banco):
    resposta = await api.post(f"{URL}/{SO_HP}/recebimentos", json={**CHECKLIST, "amostras": [amostra(1)]})

    assert resposta.status_code == 422
    assert "peças" in resposta.json()["detail"]
    assert await consultar(banco, select(SequenciaNumeroInterno)) == []


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("quantidade_pecas", 0),
        ("quantidade_pecas", "2"),
        ("urgente", "SIM"),
        ("urgente", "N"),
        ("urgente", None),
        ("procedimento_id", None),
    ],
)
async def test_dados_de_hp_so_aceitam_valores_controlados(api, banco, campo, valor):
    dados = {**DADOS_HP, campo: valor}

    resposta = await receber(api, SO_HP, 1, dados_hp=dados)

    assert resposta.status_code == 400
    assert await consultar(banco, select(Exame)) == []


async def test_procedimento_inexistente_retorna_422(api, banco):
    resposta = await receber(api, SO_HP, 1, dados_hp={**DADOS_HP, "procedimento_id": 999})

    assert resposta.status_code == 422
    assert await consultar(banco, select(SequenciaNumeroInterno)) == []


async def test_hp_grava_dados_complementares(api, banco):
    resposta = await receber(
        api,
        SO_HP,
        1,
        dados_hp={"quantidade_pecas": 3, "urgente": True, "procedimento_id": 2},
    )

    assert resposta.status_code == 201
    assert resposta.json()["exames"][0]["urgente"] is True
    exame = (await consultar(banco, select(Exame)))[0]
    assert (exame.quantidade_pecas, exame.urgente, exame.procedimento_id) == (3, True, 2)


async def test_procedimentos_vem_do_banco(api):
    resposta = await api.get("/api/recebimento/procedimentos-hp")

    assert [item["descricao"] for item in resposta.json()] == PROCEDIMENTOS_HP_INICIAIS


async def test_outra_bancada_nao_exige_dados_de_hp(api, banco):
    resposta = await api.post(
        f"{URL}/{CG_LIQUIDO}/recebimentos", json={**CHECKLIST, "amostras": [amostra(1)]}
    )

    assert resposta.status_code == 201
    exame = (await consultar(banco, select(Exame)))[0]
    assert exame.quantidade_pecas is None
    assert exame.urgente is None


async def test_co_entra_urgente(api, banco):
    resposta = await api.post(f"{URL}/{CO}/recebimentos", json={**CHECKLIST, "amostras": [amostra(1)]})

    assert resposta.status_code == 201
    assert resposta.json()["exames"][0]["urgente"] is True
    assert (await consultar(banco, select(Exame)))[0].urgente is True


async def test_ihq_guarda_referencia_ao_hp(api, banco):
    resposta = await receber(api, IHQ, 1, referencia_hp=" HP-2025/24 ")

    assert resposta.status_code == 201
    assert (await consultar(banco, select(Exame)))[0].referencia_hp == "HP-2025/24"


async def test_ihq_sem_referencia_e_aceita(api, banco):
    resposta = await receber(api, IHQ, 1)

    assert resposta.status_code == 201
    assert (await consultar(banco, select(Exame)))[0].referencia_hp is None


@pytest.mark.parametrize("referencia", ["HP 24", "HP-25/24", "HP-2025/0", "CG-2025/24", "HP-2025/"])
async def test_ihq_com_referencia_invalida_retorna_422(api, banco, referencia):
    resposta = await receber(api, IHQ, 1, referencia_hp=referencia)

    assert resposta.status_code == 422
    assert "HP-AAAA/N" in resposta.json()["detail"]
    assert await consultar(banco, select(SequenciaNumeroInterno)) == []


# --- Critério 4: recebimento parcial ---
async def test_recebendo_2_de_3_o_exame_fica_com_2(api, banco):
    resposta = await api.post(
        f"{URL}/{HP_TRES_AMOSTRAS}/recebimentos",
        json={
            **CHECKLIST,
            "amostras": [amostra(1), amostra(2), amostra(3, receber=False)],
            "dados_hp": DADOS_HP,
        },
    )

    assert resposta.status_code == 201
    amostras = await consultar(banco, select(Amostra).order_by(Amostra.numero_amostra))
    assert [(item.numero_amostra, item.recebida) for item in amostras] == [
        (1, True),
        (2, True),
        (3, False),
    ]
    assert len(await consultar(banco, select(ConferenciaAmostra))) == 2
    assert len(await consultar(banco, select(Exame))) == 1


async def test_amostra_omitida_fica_como_nao_recebida(api, banco):
    resposta = await receber(api, HP_TRES_AMOSTRAS, 1)

    assert resposta.status_code == 201
    amostras = await consultar(banco, select(Amostra))
    assert sum(item.recebida for item in amostras) == 1
    assert len(amostras) == 3


async def test_nome_e_informacoes_clinicas_nao_sao_gravados_no_banco_local(api, banco, tmp_path):
    await receber(api, SO_HP, 1)
    await devolver(api, HP_TRES_AMOSTRAS)

    exame = (await consultar(banco, select(Exame)))[0]
    assert exame.prontuario == "99000101"
    assert not hasattr(exame, "nome_paciente")
    conteudo = (tmp_path / "teste.db").read_bytes()
    assert b"99000101" in conteudo  # Confirma que a busca abaixo olha os dados gravados.
    assert "Z.Y.X.".encode() not in conteudo
    assert "W.V.U.".encode() not in conteudo
    assert TEXTO_CLINICO_DO_EXEMPLO.encode() not in conteudo


# --- Critério 5: não conformidade ---
async def test_nao_conformidade_devolve_sem_consumir_numero(api, banco):
    motivo = await primeiro_motivo(api)

    resposta = await api.post(
        f"{URL}/{SO_HP}/nao-conformidades",
        json={"motivo_id": motivo, "observacao": "Frasco sem etiqueta."},
    )

    assert resposta.status_code == 201
    dados = resposta.json()
    assert dados["motivo"] == MOTIVOS_INICIAIS[0]
    assert dados["exames"][0]["status"] == "DEVOLVIDO"
    assert dados["exames"][0]["numero_interno"] is None

    registros = await consultar(banco, select(NaoConformidade))
    assert registros[0].motivo_id == motivo
    assert registros[0].observacao == "Frasco sem etiqueta."
    assert registros[0].registrado_por == USUARIO
    assert registros[0].registrado_em is not None
    assert registros[0].resolvida is False
    assert await consultar(banco, select(SequenciaNumeroInterno)) == []

    # A devolução não pode afetar o número do próximo recebimento.
    proximo = await receber(api, CO, 1)
    assert proximo.json()["exames"][0]["numero_interno"] == "CO 1"
    proximo_hp = await receber(api, HP_TRES_AMOSTRAS, 1)
    assert proximo_hp.json()["exames"][0]["numero_interno"] == "HP 1"


async def test_nao_conformidade_guarda_cmce_e_medico(api, banco):
    resposta = await devolver(
        api, SO_HP, numero_cmce=" 12345 ", medico_solicitante=" Médico Fictício "
    )

    assert resposta.status_code == 201
    registro = (await consultar(banco, select(NaoConformidade)))[0]
    assert registro.numero_cmce == "12345"
    assert registro.medico_solicitante == "Médico Fictício"


async def test_cmce_e_medico_sao_opcionais(api, banco):
    resposta = await devolver(api, SO_HP, numero_cmce="  ")

    assert resposta.status_code == 201
    registro = (await consultar(banco, select(NaoConformidade)))[0]
    assert registro.numero_cmce is None
    assert registro.medico_solicitante is None


async def test_nao_conformidade_guarda_clinica_e_origem_sem_redigitar(api, banco):
    await devolver(api, SO_HP)

    exame = (await consultar(banco, select(Exame)))[0]
    assert exame.prontuario == "99000101"
    assert exame.origem == "Internação"
    assert exame.especialidade == "CIRURGIA GERAL"
    amostra_gravada = (await consultar(banco, select(Amostra)))[0]
    assert amostra_gravada.sigla_exame == "APECR"
    assert amostra_gravada.nome_exame


async def test_solicitacao_devolvida_recebida_de_novo_fica_resolvida(api, banco):
    await devolver(api, SO_HP)

    resposta = await receber(api, SO_HP, 1)

    assert resposta.status_code == 201
    situacoes = [exame.status for exame in await consultar(banco, select(Exame).order_by(Exame.id))]
    assert situacoes == ["DEVOLVIDO", "RECEBIDO"]
    registro = (await consultar(banco, select(NaoConformidade)))[0]
    assert registro.resolvida is True
    assert registro.resolvida_por == USUARIO
    assert registro.resolvida_em is not None
    logs = await consultar(banco, select(AuditLog).where(AuditLog.acao == "RECEBER_AMOSTRA"))
    assert json.loads(logs[0].dados_anteriores) == {
        "status": "DEVOLVIDO",
        "nao_conformidades_pendentes": [registro.id],
    }
    assert json.loads(logs[0].dados_novos)["nao_conformidades_resolvidas"] == [registro.id]


async def test_receber_outra_bancada_nao_resolve_a_devolucao(api, banco):
    await devolver(api, CO_E_HP)

    await receber(api, CO_E_HP, 1)

    registros = await consultar(banco, select(NaoConformidade).order_by(NaoConformidade.id))
    exames = {
        exame.id: exame.tipo for exame in await consultar(banco, select(Exame))
    }
    situacao = {exames[registro.exame_id]: registro.resolvida for registro in registros}
    assert situacao == {"CO": True, "HP": False}


async def test_nao_conformidade_com_motivo_invalido_retorna_422(api):
    resposta = await api.post(
        f"{URL}/{SO_HP}/nao-conformidades", json={"motivo_id": 9999, "observacao": "Teste"}
    )

    assert resposta.status_code == 422


async def test_nao_conformidade_sem_observacao_e_bloqueada(api):
    motivo = await primeiro_motivo(api)

    vazia = await api.post(
        f"{URL}/{SO_HP}/nao-conformidades", json={"motivo_id": motivo, "observacao": ""}
    )
    so_espacos = await api.post(
        f"{URL}/{SO_HP}/nao-conformidades", json={"motivo_id": motivo, "observacao": "   "}
    )

    assert vazia.status_code == 400
    assert so_espacos.status_code == 422


async def test_nao_conformidade_de_solicitacao_ja_recebida_retorna_409(api):
    await receber(api, SO_HP, 1)

    resposta = await devolver(api, SO_HP)

    assert resposta.status_code == 409
    assert "HP 1" in resposta.json()["detail"]


async def test_motivos_iniciais_sao_os_14_da_planilha(api):
    resposta = await api.get("/api/recebimento/motivos-nao-conformidade")

    descricoes = [motivo["descricao"] for motivo in resposta.json()]
    assert descricoes == MOTIVOS_INICIAIS
    assert len(descricoes) == 14
    assert descricoes[-1] == "Outra"


# --- Critério 6: sequência por tipo e por ano ---
async def test_numeros_sao_sequenciais_por_tipo(api):
    primeiro = await receber(api, SO_HP, 1)
    segundo = await receber(api, HP_TRES_AMOSTRAS, 1, 2, 3)
    citologia = await receber(api, CG_LIQUIDO, 1)

    assert primeiro.json()["exames"][0]["numero_interno"] == "HP 1"
    assert segundo.json()["exames"][0]["numero_interno"] == "HP 2"
    assert citologia.json()["exames"][0]["numero_interno"] == "CG 1"


async def test_numero_reinicia_na_virada_do_ano_de_recife(api, banco, monkeypatch):
    # 31/12/2026 às 22h em Recife ainda é 2026, embora já seja 2027 em UTC.
    monkeypatch.setattr(
        recebimento_controller, "_agora", lambda: datetime(2027, 1, 1, 1, 0, tzinfo=timezone.utc)
    )
    fim_de_ano = await receber(api, SO_HP, 1)
    assert fim_de_ano.json()["exames"][0]["numero_interno"] == "HP 1"
    assert (await consultar(banco, select(Exame)))[0].ano == 2026

    monkeypatch.setattr(
        recebimento_controller, "_agora", lambda: datetime(2027, 1, 1, 1, 30, tzinfo=timezone.utc)
    )
    mesmo_ano = await receber(api, HP_TRES_AMOSTRAS, 1)
    assert mesmo_ano.json()["exames"][0]["numero_interno"] == "HP 2"

    # 01/01/2027 às 00h30 em Recife: a sequência reinicia.
    monkeypatch.setattr(
        recebimento_controller, "_agora", lambda: datetime(2027, 1, 1, 3, 30, tzinfo=timezone.utc)
    )
    ano_novo = await receber(api, COM_LACUNAS, 3)
    assert ano_novo.json()["exames"][0]["numero_interno"] == "HP 1"
    anos = sorted(exame.ano for exame in await consultar(banco, select(Exame)))
    assert anos == [2026, 2026, 2027]


async def test_duas_bancadas_geram_um_numero_por_bancada(api):
    resposta = await receber(api, CO_E_HP, 1, 2)

    assert resposta.status_code == 201
    assert sorted(exame["numero_interno"] for exame in resposta.json()["exames"]) == ["CO 1", "HP 1"]


async def test_tres_bancadas_geram_tres_numeros(api):
    resposta = await receber(api, TRES_BANCADAS, 1, 2, 3)

    assert resposta.status_code == 201
    assert sorted(exame["numero_interno"] for exame in resposta.json()["exames"]) == [
        "CCV 1",
        "CG 1",
        "HP 1",
    ]


async def test_duas_siglas_na_mesma_bancada_ficam_em_um_exame(api, banco):
    resposta = await receber(api, DUAS_SIGLAS_NO_HP, 1, 2)

    assert [exame["numero_interno"] for exame in resposta.json()["exames"]] == ["HP 1"]
    amostras = await consultar(banco, select(Amostra).order_by(Amostra.numero_amostra))
    assert [item.sigla_exame for item in amostras] == ["APECR", "MBIOP"]


async def test_bancada_nao_marcada_nao_consome_numero_e_pode_ser_recebida_depois(api, banco):
    so_co = await receber(api, CO_E_HP, 1)
    assert [exame["numero_interno"] for exame in so_co.json()["exames"]] == ["CO 1"]
    sequencias = await consultar(banco, select(SequenciaNumeroInterno))
    assert [sequencia.tipo for sequencia in sequencias] == ["CO"]

    consulta = await api.get(f"{URL}/{CO_E_HP}")
    por_numero = {item["numero_amostra"]: item for item in consulta.json()["amostras"]}
    assert por_numero[1]["recebivel"] is False
    assert por_numero[2]["recebivel"] is True

    hp = await receber(api, CO_E_HP, 2)
    assert hp.json()["exames"][0]["numero_interno"] == "HP 1"


async def test_ihq_usa_bancada_ihq_e_numero_ih(api, banco):
    resposta = await receber(api, IHQ, 1)

    assert resposta.json()["exames"][0]["numero_interno"] == "IH 1"
    assert resposta.json()["exames"][0]["tipo"] == "IHQ"
    assert (await consultar(banco, select(Exame)))[0].tipo == "IHQ"


async def test_recebimento_duplicado_retorna_409_e_nao_consome_numero(api, banco):
    await receber(api, SO_HP, 1)

    resposta = await receber(api, SO_HP, 1)

    assert resposta.status_code == 409
    assert "HP 1" in resposta.json()["detail"]
    sequencia = (await consultar(banco, select(SequenciaNumeroInterno)))[0]
    assert sequencia.ultimo_numero == 1


# --- Critério 7: simultaneidade ---
class ProviderDeCarga(SolicitacaoProviderInterface):
    """Gera uma solicitação HP para qualquer código, para simular muitos recebimentos."""

    async def obter_solicitacao_por_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
        """Retorna uma solicitação fictícia com uma amostra HP."""
        return await ProviderFixo([item_fixo()]).obter_solicitacao_por_codigo(codigo)

    async def listar_solicitacoes(self, *_: Any) -> Dict[str, Any]:
        """A carga não usa a lista."""
        return {"total": 0, "solicitacoes": []}


@pytest.fixture
def provider_de_carga():
    """Troca o provider de solicitações pelo gerador de carga."""
    app.dependency_overrides[_get_solicitacao_csv_provider] = ProviderDeCarga
    yield
    app.dependency_overrides.pop(_get_solicitacao_csv_provider, None)


async def test_50_recebimentos_simultaneos_nao_repetem_nem_pulam_numeros(
    api, banco, provider_de_carga
):
    respostas = await asyncio.gather(
        *[receber(api, str(9100000 + indice), 1) for indice in range(50)]
    )

    assert [resposta.status_code for resposta in respostas] == [201] * 50
    numeros = sorted(resposta.json()["exames"][0]["numero_interno"] for resposta in respostas)
    assert numeros == sorted(f"HP {numero}" for numero in range(1, 51))
    sequencia = (await consultar(banco, select(SequenciaNumeroInterno)))[0]
    assert sequencia.ultimo_numero == 50
    assert len(await consultar(banco, select(AuditLog))) == 50


async def test_50_leituras_simultaneas_da_mesma_etiqueta_geram_um_so_exame(
    api, banco, provider_de_carga
):
    respostas = await asyncio.gather(*[receber(api, "9100000", 1) for _ in range(50)])

    codigos = sorted(resposta.status_code for resposta in respostas)
    assert codigos == [201] + [409] * 49
    assert len(await consultar(banco, select(Exame))) == 1
    sequencia = (await consultar(banco, select(SequenciaNumeroInterno)))[0]
    assert sequencia.ultimo_numero == 1


# --- Critério 8: autenticação ---
@pytest.mark.parametrize(
    "metodo,rota",
    [
        ("GET", "/api/recebimento/motivos-nao-conformidade"),
        ("GET", "/api/recebimento/procedimentos-hp"),
        ("GET", URL),
        ("GET", f"{URL}/{SO_HP}"),
        ("POST", f"{URL}/{SO_HP}/recebimentos"),
        ("POST", f"{URL}/{SO_HP}/nao-conformidades"),
    ],
)
async def test_requisicao_sem_token_recebe_401(anonimo, metodo, rota):
    resposta = await anonimo.request(metodo, rota, json={})

    assert resposta.status_code == 401


# --- Critério 9: auditoria ---
async def test_recebimento_gera_auditoria_completa(api, banco):
    await receber(api, SO_HP, 1)

    logs = await consultar(banco, select(AuditLog))
    assert len(logs) == 1
    log = logs[0]
    assert log.usuario == USUARIO
    assert log.categoria == "NEGOCIO_CLINICO"
    assert log.acao == "RECEBER_AMOSTRA"
    assert log.ip_origem == "127.0.0.1"
    assert json.loads(log.dados_anteriores) == {"status": None}
    novos = json.loads(log.dados_novos)
    assert novos["status"] == "RECEBIDO"
    assert novos["numero_interno"] == "HP 1"
    assert novos["amostras_recebidas"] == [1]
    assert novos["quantidade_pecas"] == DADOS_HP["quantidade_pecas"]
    assert novos["urgente"] is False
    assert novos["checklist"] == CHECKLIST


async def test_nao_conformidade_gera_auditoria_completa(api, banco):
    await devolver(api, SO_HP, numero_cmce="12345")

    logs = await consultar(banco, select(AuditLog))
    assert len(logs) == 1
    log = logs[0]
    assert log.categoria == "NEGOCIO_CLINICO"
    assert log.acao == "REGISTRAR_NAO_CONFORMIDADE"
    assert log.ip_origem == "127.0.0.1"
    assert json.loads(log.dados_anteriores) == {"status": None}
    novos = json.loads(log.dados_novos)
    assert novos["status"] == "DEVOLVIDO"
    assert novos["observacao"] == "Frasco sem etiqueta."
    assert novos["numero_cmce"] == "12345"


async def test_duas_bancadas_geram_uma_auditoria_por_exame(api, banco):
    await receber(api, CO_E_HP, 1, 2)

    total = await consultar(banco, select(func.count()).select_from(AuditLog))
    assert total == [2]


async def test_mutacao_recusada_nao_gera_auditoria(api, banco):
    await api.post(f"{URL}/{SO_HP}/recebimentos", json={"amostras": [amostra(1)]})

    assert await consultar(banco, select(AuditLog)) == []


# --- Leitura da view: CSV e Postgres ---
async def test_csv_de_exemplo_tem_o_cabecalho_da_view():
    cabecalho = CSV_EXEMPLO.read_text(encoding="utf-8").splitlines()[0]

    assert tuple(cabecalho.split(",")) == COLUNAS_VIEW


async def test_csv_sem_coluna_obrigatoria_retorna_503(tmp_path):
    arquivo = tmp_path / "invalido.csv"
    arquivo.write_text("codigo_solicitacao,numero_amostra\n9000101,1\n", encoding="utf-8")

    with pytest.raises(HTTPException) as erro:
        await SolicitacaoCsvProvider(str(arquivo)).obter_solicitacao_por_codigo("9000101")

    assert erro.value.status_code == 503
    assert "layout" in erro.value.detail


async def test_csv_inexistente_levanta_erro_claro(tmp_path):
    with pytest.raises(RuntimeError):
        SolicitacaoCsvProvider(str(tmp_path / "nao_existe.csv"))


@pytest.mark.parametrize(
    "valor,esperado",
    [
        ("9º  SUL", "9º SUL"),
        ("UAP: HISTOPATOLÓGICO​", "UAP: HISTOPATOLÓGICO"),
        ("  texto​  com ﻿ lixo ", "texto com lixo"),
        ("", ""),
        (None, ""),
    ],
)
async def test_texto_do_aghu_e_limpo(valor, esperado):
    assert limpar_texto(valor) == esperado


@pytest.mark.parametrize(
    "valor,esperado",
    [
        ("Linha 1\nLinha 2", "Linha 1\nLinha 2"),
        ("  Linha  1 \r\n\r\n\u200bLinha 2\r\n", "Linha 1\nLinha 2"),
        ("   ", ""),
        (None, ""),
    ],
)
async def test_informacoes_clinicas_preservam_as_quebras_de_linha(valor, esperado):
    assert limpar_texto_com_linhas(valor) == esperado


async def test_solicitacao_montada_mantem_as_linhas_do_texto_clinico():
    solicitacao = montar_solicitacao([linha_da_view(informacoes_clinica="Linha 1\r\nLinha 2  fim")])

    assert solicitacao["informacoes_clinica"] == "Linha 1\nLinha 2 fim"


@pytest.mark.parametrize(
    "valor,esperado",
    [
        ("31/12/1980", "1980-12-31"),
        (date(1980, 12, 31), "1980-12-31"),
        (datetime(1980, 12, 31, 8, 0), "1980-12-31"),
        ("", None),
        (None, None),
        ("31/02/1980", None),
        ("1980-12-31", None),
    ],
)
async def test_data_do_aghu_e_convertida(valor, esperado):
    assert converter_data(valor) == esperado


class SessaoFalsa:
    """Imita a sessão do banco do AGHU, devolvendo linhas da view com tipos do Postgres."""

    def __init__(self, linhas: List[Dict[str, Any]]) -> None:
        """Guarda as linhas que a consulta deve devolver."""
        self.linhas = linhas
        self.sql = ""
        self.parametros: Dict[str, Any] = {}

    async def execute(self, sql: Any, parametros: Dict[str, Any]) -> "SessaoFalsa":
        """Registra a consulta e devolve a própria sessão como resultado."""
        self.sql = str(sql)
        self.parametros = parametros
        return self

    def mappings(self) -> "SessaoFalsa":
        """Imita Result.mappings()."""
        return self

    def all(self) -> List[Dict[str, Any]]:
        """Imita MappingResult.all()."""
        return self.linhas

    def scalar_one(self) -> int:
        """Imita Result.scalar_one() na contagem, com um total fixo."""
        return 42


def linha_da_view(**valores: Any) -> Dict[str, Any]:
    """Monta uma linha da view com os tipos do Postgres."""
    return {
        "codigo_solicitacao": 9000101,
        "numero_amostra": 2,
        "cod_status_item": "CO",
        "status_item_exame": "COLETADO",
        "data_solicitacao": date(2026, 3, 2),
        "nome_paciente": "Z.Y.X.",
        "data_nascimento": date(1980, 5, 14),
        "prontuario": None,
        "especialidade": None,
        "convenio": "SUS",
        "origem": "Paciente Externo",
        "unidade": "UAP: HISTOPATOLÓGICO​",
        "codigo_lab": 207,
        "informacoes_clinica": None,
        "sigla_exame": "APECR",
        "nome_exame": "ANATOMOPATOLÓGICO",
        "descricao_material": None,
        **valores,
    }


async def test_provider_postgres_lista_com_filtros_e_paginacao():
    sessao = SessaoFalsa(
        [
            linha_da_view(codigo_solicitacao=9000102, numero_amostra=1),
            linha_da_view(codigo_solicitacao=9000102, numero_amostra=2),
            linha_da_view(codigo_solicitacao=9000101, numero_amostra=1),
        ]
    )

    resultado = await SolicitacaoPostgresProvider(sessao).listar_solicitacoes(3, 10, ["CO"], ["207"])

    assert resultado["total"] == 42
    assert [item["codigo"] for item in resultado["solicitacoes"]] == ["9000102", "9000101"]
    assert len(resultado["solicitacoes"][0]["itens"]) == 2
    assert "vw_solicitacao" in sessao.sql
    assert sessao.parametros == {
        "codigos_lab": ["207"],
        "filtrar_status": True,
        "codigos_status": ["CO"],
        "limite": 10,
        "deslocamento": 20,
    }


async def test_provider_postgres_le_a_view_com_parametro_e_tipos_nativos():
    sessao = SessaoFalsa([linha_da_view()])

    solicitacao = await SolicitacaoPostgresProvider(sessao).obter_solicitacao_por_codigo("9000101")

    assert "vw_solicitacao" in sessao.sql
    assert sessao.parametros == {"codigo": "9000101"}
    assert solicitacao["codigo"] == "9000101"
    assert solicitacao["data_nascimento"] == "1980-05-14"
    assert solicitacao["prontuario"] is None
    assert solicitacao["unidade"] == "UAP: HISTOPATOLÓGICO"
    assert solicitacao["itens"][0]["codigo_lab"] == "207"
    assert solicitacao["itens"][0]["numero_amostra"] == 2


async def test_montar_solicitacao_sem_linhas_retorna_none():
    assert montar_solicitacao([]) is None


# --- RN-01: AGHU somente leitura ---
async def test_sql_de_solicitacao_nao_tem_comando_de_escrita():
    pasta = Path(__file__).parent.parent / "src" / "providers" / "sql" / "solicitacao"
    arquivos = list(pasta.glob("*.sql"))
    assert arquivos

    for arquivo in arquivos:
        sql = re.sub(r"--[^\n]*|/\*.*?\*/", "", arquivo.read_text(encoding="utf-8"), flags=re.DOTALL)
        assert not re.search(
            r"\b(INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|TRUNCATE|CREATE)\b", sql, re.IGNORECASE
        ), arquivo.name
