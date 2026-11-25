# tests/test_exame_csv_provider.py
from pathlib import Path

import pytest

from src.providers.implementations.exame_csv_provider import ExameCsvProvider
from src.providers.interfaces.exame_provider_interface import ExameProviderInterface


EXPECTED_OFFICIAL_COLUMNS = {
    "prontuario",
    "nome",
    "telefone",
    "cidade",
    "estado",
    "codigo_solicitacao",
    "data_solicitao",
    "data_solicitacao",
    "unidade_solicitante",
    "codigo_exame",
    "nome_exame",
    "id_funcionario",
    "nome_funcionario",
}


def test_exame_csv_provider_implements_interface() -> None:
    """Garante que ExameCsvProvider implementa ExameProviderInterface."""
    provider = ExameCsvProvider()
    assert isinstance(provider, ExameProviderInterface)
    assert provider.csv_path == "data/exames_aghu_mock.csv"


def test_exame_csv_provider_missing_file_raises_runtime_error(tmp_path: Path) -> None:
    """Garante que um caminho de CSV inexistente dispara RuntimeError na inicialização."""
    missing_csv = tmp_path / "nao_existe.csv"
    with pytest.raises(RuntimeError, match="Arquivo CSV de exames não encontrado"):
        ExameCsvProvider(csv_path=str(missing_csv))


@pytest.mark.asyncio
async def test_listar_exames_mock_csv_completo() -> None:
    """Valida a leitura completa do CSV oficial mockado do AGHU."""
    provider = ExameCsvProvider()
    exames = await provider.listar_exames()

    assert len(exames) == 24
    for row in exames:
        assert EXPECTED_OFFICIAL_COLUMNS.issubset(row.keys())
        assert row["data_solicitao"] == row["data_solicitacao"]
        assert isinstance(row["id_funcionario"], int)


@pytest.mark.asyncio
async def test_listar_exames_normaliza_aspas_e_virgulas_no_mock() -> None:
    """Valida campos com vírgulas entre aspas e aspas escapadas RFC 4180 no CSV oficial."""
    provider = ExameCsvProvider()
    exames = await provider.listar_exames()
    por_codigo = {row["codigo_solicitacao"]: row for row in exames}

    assert (
        por_codigo["890002"]["nome_exame"]
        == "CINTILOGRAFIA MIOCARDICA (ESTRESSE FARMACOLOGICO, DIPIRIDAMOL)"
    )
    assert (
        por_codigo["890007"]["nome_exame"]
        == "COLONOSCOPIA COM BIOPSIA, SE NECESSARIO"
    )
    assert (
        por_codigo["890011"]["nome_exame"]
        == 'UDI: ULTRASSONOGRAFIA, "TRANSFONTANELA"'
    )


@pytest.mark.asyncio
async def test_listar_exames_prontuario_anulavel_no_mock() -> None:
    """Valida que prontuários vazios (com e sem aspas) no CSV oficial viram None."""
    provider = ExameCsvProvider()

    sol_aspas_vazias = await provider.buscar_por_solicitacao("890016")
    assert len(sol_aspas_vazias) == 1
    assert sol_aspas_vazias[0]["prontuario"] is None
    assert sol_aspas_vazias[0]["nome"] == "PACIENTE ANONIMIZADO 13"

    sol_sem_aspas = await provider.buscar_por_solicitacao("890017")
    assert len(sol_sem_aspas) == 1
    assert sol_sem_aspas[0]["prontuario"] is None
    assert sol_sem_aspas[0]["nome"] == "PACIENTE ANONIMIZADO 14"


@pytest.mark.asyncio
async def test_buscar_por_solicitacao_multiplos_itens_e_trim() -> None:
    """Valida busca por código de solicitação com múltiplos exames e espaços nas bordas."""
    provider = ExameCsvProvider()

    itens = await provider.buscar_por_solicitacao("890001")
    assert len(itens) == 2
    assert {item["codigo_exame"] for item in itens} == {"USAX", "HEMO"}
    assert all(item["prontuario"] == "1023456" for item in itens)
    assert all(item["id_funcionario"] == 10421 for item in itens)

    itens_com_espaco = await provider.buscar_por_solicitacao("  890001  ")
    assert itens_com_espaco == itens


@pytest.mark.asyncio
async def test_buscar_por_solicitacao_inexistente_ou_vazio() -> None:
    """Valida retorno vazio para códigos de solicitação inexistentes ou em branco."""
    provider = ExameCsvProvider()

    assert await provider.buscar_por_solicitacao("999999") == []
    assert await provider.buscar_por_solicitacao("") == []
    assert await provider.buscar_por_solicitacao("   ") == []


@pytest.mark.asyncio
async def test_buscar_por_prontuario_multiplas_solicitacoes_e_trim() -> None:
    """Valida busca por prontuário retornando todas as solicitações do paciente."""
    provider = ExameCsvProvider()

    exames = await provider.buscar_por_prontuario("1045890")
    assert len(exames) == 2
    assert [e["codigo_solicitacao"] for e in exames] == ["890002", "890003"]
    assert {e["codigo_exame"] for e in exames} == {"CMDIP", "CMREP"}

    exames_com_espaco = await provider.buscar_por_prontuario(" 1045890 ")
    assert exames_com_espaco == exames


@pytest.mark.asyncio
async def test_buscar_por_prontuario_inexistente_vazio_ou_none() -> None:
    """Valida que prontuário inexistente, vazio ou None retorna lista vazia sem casar nulos."""
    provider = ExameCsvProvider()

    assert await provider.buscar_por_prontuario("0000000") == []
    assert await provider.buscar_por_prontuario("") == []
    assert await provider.buscar_por_prontuario("   ") == []
    assert await provider.buscar_por_prontuario(None) == []  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_custom_csv_normalizacao_aspas_duplas_e_rfc4180(tmp_path: Path) -> None:
    """Valida remoção de aspas duplas residuais, espaços e unescape RFC 4180."""
    csv_file = tmp_path / "aspas.csv"
    csv_file.write_text(
        (
            "prontuario,nome,codigo_solicitacao,data_solicitao,nome_exame,id_funcionario\n"
            ' "123456" , "PACIENTE TESTE" , "900001" , "2026-11-20 10:00:00" ,'
            '"""EXAME ""ESPECIAL"", COM ASPAS""", "42" \n'
            '"654321","PACIENTE RFC","900002","2026-11-21 11:00:00",'
            '"DOPPLER, ""ARTERIAL"" E VENOSO","99"\n'
        ),
        encoding="utf-8",
    )

    provider = ExameCsvProvider(csv_path=str(csv_file))
    rows = await provider.listar_exames()

    assert len(rows) == 2
    assert rows[0]["prontuario"] == "123456"
    assert rows[0]["nome"] == "PACIENTE TESTE"
    assert rows[0]["codigo_solicitacao"] == "900001"
    assert rows[0]["nome_exame"] == 'EXAME "ESPECIAL", COM ASPAS'
    assert rows[0]["id_funcionario"] == 42

    assert rows[1]["nome_exame"] == 'DOPPLER, "ARTERIAL" E VENOSO'
    assert rows[1]["id_funcionario"] == 99


@pytest.mark.asyncio
async def test_custom_csv_alias_data_solicitacao_bidirecional(tmp_path: Path) -> None:
    """Valida o alias bidirecional entre data_solicitao e data_solicitacao."""
    csv_corrigido = tmp_path / "data_corrigida.csv"
    csv_corrigido.write_text(
        (
            "prontuario,codigo_solicitacao,data_solicitacao,id_funcionario\n"
            '"1001","910001","2026-11-22 08:30:00","500"\n'
        ),
        encoding="utf-8",
    )

    provider_corrigido = ExameCsvProvider(csv_path=str(csv_corrigido))
    rows_corrigido = await provider_corrigido.listar_exames()
    assert len(rows_corrigido) == 1
    assert rows_corrigido[0]["data_solicitacao"] == "2026-11-22 08:30:00"
    assert rows_corrigido[0]["data_solicitao"] == "2026-11-22 08:30:00"

    csv_ambas = tmp_path / "data_ambas.csv"
    csv_ambas.write_text(
        (
            "prontuario,codigo_solicitacao,data_solicitao,data_solicitacao,id_funcionario\n"
            '"1002","910002","2026-11-22 08:00:00","2026-11-22 09:00:00","501"\n'
        ),
        encoding="utf-8",
    )

    provider_ambas = ExameCsvProvider(csv_path=str(csv_ambas))
    rows_ambas = await provider_ambas.listar_exames()
    assert rows_ambas[0]["data_solicitao"] == "2026-11-22 08:00:00"
    assert rows_ambas[0]["data_solicitacao"] == "2026-11-22 09:00:00"


@pytest.mark.asyncio
async def test_custom_csv_id_funcionario_cast_int_none_e_invalido(tmp_path: Path) -> None:
    """Valida conversão de id_funcionario para int, None (vazio/ausente) e fallback para texto."""
    csv_file = tmp_path / "id_funcionario.csv"
    csv_file.write_text(
        (
            "prontuario,codigo_solicitacao,data_solicitao,id_funcionario\n"
            '"2001","920001","2026-11-23 08:00:00"," 00745 "\n'
            '"2002","920002","2026-11-23 08:05:00",""\n'
            '"2003","920003","2026-11-23 08:10:00",   \n'
            '"2004","920004","2026-11-23 08:15:00","NAO_NUMERICO"\n'
            '"2005","920005","2026-11-23 08:20:00"\n'
        ),
        encoding="utf-8",
    )

    provider = ExameCsvProvider(csv_path=str(csv_file))
    rows = await provider.listar_exames()

    assert rows[0]["id_funcionario"] == 745
    assert isinstance(rows[0]["id_funcionario"], int)
    assert rows[1]["id_funcionario"] is None
    assert rows[2]["id_funcionario"] is None
    assert rows[3]["id_funcionario"] == "NAO_NUMERICO"
    assert rows[4]["id_funcionario"] is None


@pytest.mark.asyncio
async def test_custom_csv_prontuario_espacos_bom_colunas_extras_e_vazio(
    tmp_path: Path,
) -> None:
    """Valida BOM UTF-8, cabeçalhos com espaços, prontuário em branco, colunas extras e CSV vazio."""
    csv_bom = tmp_path / "bom_edge_cases.csv"
    csv_bom.write_text(
        (
            "\ufeff prontuario , codigo_solicitacao , data_solicitao , id_funcionario \n"
            '"   ","930001","2026-11-24 10:00:00","100","COLUNA_EXTRA_IGNORADA"\n'
            ',"930002","2026-11-24 10:15:00",""\n'
        ),
        encoding="utf-8",
    )

    provider_bom = ExameCsvProvider(csv_path=str(csv_bom))
    rows = await provider_bom.listar_exames()

    assert len(rows) == 2
    assert None not in rows[0]
    assert "prontuario" in rows[0]
    assert rows[0]["prontuario"] is None
    assert rows[0]["codigo_solicitacao"] == "930001"
    assert rows[0]["id_funcionario"] == 100
    assert rows[1]["prontuario"] is None
    assert rows[1]["id_funcionario"] is None

    csv_vazio = tmp_path / "vazio.csv"
    csv_vazio.write_text(
        "prontuario,codigo_solicitacao,data_solicitao,id_funcionario\n",
        encoding="utf-8",
    )
    provider_vazio = ExameCsvProvider(csv_path=str(csv_vazio))
    assert await provider_vazio.listar_exames() == []
    assert await provider_vazio.buscar_por_solicitacao("930001") == []
    assert await provider_vazio.buscar_por_prontuario("123456") == []
