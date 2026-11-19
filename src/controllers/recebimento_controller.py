import logging
import re
from datetime import date, datetime, timezone
from math import ceil
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..helpers.audit_helper import registrar_auditoria
from ..helpers.etiqueta_helper import interpretar_codigo_lido
from ..models.exame import STATUS_DEVOLVIDO, STATUS_RECEBIDO
from ..providers.interfaces.recebimento_provider_interface import RecebimentoProviderInterface
from ..providers.interfaces.solicitacao_provider_interface import SolicitacaoProviderInterface

logger = logging.getLogger("recebimento")

BANCADA_HP = "HP"
BANCADA_CO = "CO"
BANCADA_IHQ = "IHQ"
ORIGEM_PACIENTE_EXTERNO = "Paciente Externo"
CATEGORIA_AUDITORIA = "NEGOCIO_CLINICO"
# O ano do nº interno segue o calendário do hospital, não o UTC.
FUSO_HOSPITAL = ZoneInfo("America/Recife")
ITENS_CHECKLIST = ("sigla_confere", "descricao_confere", "recipientes_confere")
PADRAO_REFERENCIA_HP = re.compile(r"^HP-\d{4}/[1-9]\d*$")
SITUACAO_AGUARDANDO = "AGUARDANDO"
SITUACAO_PARCIAL = "PARCIAL"
SITUACAO_RECEBIDA = "RECEBIDA"
SITUACAO_DEVOLVIDA = "DEVOLVIDA"
SITUACAO_BLOQUEADA = "BLOQUEADA"


def _agora() -> datetime:
    """Retorna a data e a hora atuais em UTC. Isolada para os testes controlarem o relógio."""
    return datetime.now(timezone.utc)


def _ano_do_hospital(momento: datetime) -> int:
    """Retorna o ano do momento informado no fuso do hospital."""
    return momento.astimezone(FUSO_HOSPITAL).year


def _calcular_idade(data_nascimento: Optional[str], hoje: date) -> Optional[int]:
    """Calcula a idade em anos; retorna None se a data estiver ausente ou inválida."""
    if not data_nascimento:
        return None
    try:
        nascimento = date.fromisoformat(data_nascimento)
    except ValueError:
        return None
    return hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))


def _formatar_momento(momento: datetime) -> str:
    """Formata o momento em ISO 8601 UTC. O SQLite devolve datas sem fuso, sempre em UTC."""
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _itens_das_bancadas(
    solicitacao: Dict[str, Any], bancadas: Dict[str, Dict[str, str]]
) -> List[Dict[str, Any]]:
    """Mantém só os itens de laboratórios mapeados, acrescentando bancada e prefixo."""
    return [
        {**item, **bancadas[item["codigo_lab"]]}
        for item in solicitacao["itens"]
        if item["codigo_lab"] in bancadas
    ]


def _exame_para_resposta(exame: Dict[str, Any]) -> Dict[str, Any]:
    """Formata um exame para a resposta da API."""
    resposta = {
        "numero_interno": exame["numero_interno"],
        "tipo": exame["tipo"],
        "status": exame["status"],
        "urgente": exame["urgente"],
        "recebido_por": exame["recebido_por"],
        "recebido_em": _formatar_momento(exame["recebido_em"]),
    }
    if "amostras" in exame:
        resposta["amostras"] = exame["amostras"]
    return resposta


async def _resolver_solicitacao(
    codigo: str, provider: SolicitacaoProviderInterface
) -> Tuple[Dict[str, Any], Optional[int]]:
    """
    Interpreta o código lido e busca a solicitação.

    Retorna a solicitação e o número da amostra lida. Responde 422 se o formato for inválido
    e 404 se a solicitação ou a amostra não existirem.
    """
    interpretado = interpretar_codigo_lido(codigo)
    if interpretado is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Código lido inválido: {codigo.strip()}. Bipe a etiqueta da solicitação.",
        )
    codigo_solicitacao, numero_amostra = interpretado

    # Só `None` significa que a solicitação não existe. Falhas de leitura chegam como
    # HTTPException (503) levantada pelo provider e seguem direto para o cliente.
    solicitacao = await provider.obter_solicitacao_por_codigo(codigo_solicitacao)
    if solicitacao is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Solicitação {codigo.strip()} não encontrada no AGHU.",
        )
    if numero_amostra is not None and not any(
        item["numero_amostra"] == numero_amostra for item in solicitacao["itens"]
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Amostra {numero_amostra} não encontrada na solicitação {codigo_solicitacao}.",
        )
    return solicitacao, numero_amostra


async def _exigir_itens_das_bancadas(
    solicitacao: Dict[str, Any], recebimento_provider: RecebimentoProviderInterface
) -> List[Dict[str, Any]]:
    """Retorna os itens das bancadas configuradas ou responde 422 se não houver nenhum."""
    bancadas = await recebimento_provider.listar_bancadas()
    itens = _itens_das_bancadas(solicitacao, bancadas)
    if not itens:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"A solicitação {solicitacao['codigo']} não tem itens da Anatomia Patológica "
                "(HP, CO, IHQ, CG ou CCV)."
            ),
        )
    return itens


def _numero_recebido_por_tipo(exames: List[Dict[str, Any]]) -> Dict[str, str]:
    """Retorna o nº interno de cada tipo que já foi recebido na solicitação."""
    return {
        exame["tipo"]: exame["numero_interno"]
        for exame in exames
        if exame["status"] == STATUS_RECEBIDO
    }


def _status_anterior_por_tipo(exames: List[Dict[str, Any]]) -> Dict[str, str]:
    """Retorna o último status registrado para cada tipo, para a trilha de auditoria."""
    return {exame["tipo"]: exame["status"] for exame in exames}


def _motivo_de_bloqueio(
    item: Dict[str, Any],
    solicitacao: Dict[str, Any],
    status_item: Dict[str, Dict[str, Any]],
) -> Optional[str]:
    """Retorna por que a amostra não pode ser recebida, ou None se ela puder."""
    configuracao = status_item.get(item["cod_status_item"])
    if configuracao is None:
        return (
            f"Status {item['cod_status_item']} não configurado no sistema. "
            "Registre a não conformidade."
        )
    if not configuracao["permite_recebimento"]:
        return (
            f"Item {configuracao['descricao']} no AGHU não pode ser recebido. "
            "Se o frasco chegou, registre a não conformidade."
        )
    if not solicitacao["prontuario"] and solicitacao["origem"] != ORIGEM_PACIENTE_EXTERNO:
        return "Prontuário ausente no AGHU. Registre a não conformidade."
    return None


async def listar_motivos(provider: RecebimentoProviderInterface) -> List[Dict[str, Any]]:
    """Lista os motivos de não conformidade ativos."""
    return await provider.listar_motivos()


async def listar_procedimentos_hp(provider: RecebimentoProviderInterface) -> List[Dict[str, Any]]:
    """Lista os procedimentos de HP ativos."""
    return await provider.listar_procedimentos_hp()

def _solicitacao_urgente(exames: List[Dict[str, Any]], itens: List[Dict[str, Any]]) -> bool:
    """Regra única de urgência: exame gravado como urgente ou amostra de CO (CARE-RF007)."""
    return any(exame["urgente"] for exame in exames) or any(
        item["bancada"] == BANCADA_CO for item in itens
    )

def _situacao_na_lista(
    recebiveis: int, recebidos: Dict[str, str], exames: List[Dict[str, Any]]
) -> str:
    """Resume em que ponto a solicitação está, a partir das amostras e dos exames registrados."""
    if recebiveis == 0:
        return SITUACAO_RECEBIDA if recebidos else SITUACAO_BLOQUEADA
    if recebidos:
        return SITUACAO_PARCIAL
    if any(exame["status"] == STATUS_DEVOLVIDO for exame in exames):
        return SITUACAO_DEVOLVIDA
    return SITUACAO_AGUARDANDO


def _resumo_para_lista(
    solicitacao: Dict[str, Any],
    exames: List[Dict[str, Any]],
    bancadas: Dict[str, Dict[str, str]],
    status_item: Dict[str, Dict[str, Any]],
    hoje: date,
) -> Dict[str, Any]:
    """Monta a linha de uma solicitação na lista inicial da Recepção."""
    itens = _itens_das_bancadas(solicitacao, bancadas)
    recebidos = _numero_recebido_por_tipo(exames)
    recebiveis = sum(
        item["bancada"] not in recebidos
        and _motivo_de_bloqueio(item, solicitacao, status_item) is None
        for item in itens
    )
    return {
        "codigo": solicitacao["codigo"],
        "data_solicitacao": solicitacao["data_solicitacao"],
        "paciente": {
            "nome": solicitacao["nome_paciente"],
            "prontuario": solicitacao["prontuario"],
            "idade": _calcular_idade(solicitacao["data_nascimento"], hoje),
        },
        "urgente": _solicitacao_urgente(exames, itens),
        "origem": solicitacao["origem"],
        "especialidade": solicitacao["especialidade"],
        "unidade": solicitacao["unidade"],
        "bancadas": sorted({item["bancada"] for item in itens}),
        "total_amostras": len(itens),
        "amostras_recebiveis": recebiveis,
        "numeros_internos": sorted(recebidos.values()),
        "situacao": _situacao_na_lista(recebiveis, recebidos, exames),
    }


async def listar_solicitacoes(
    pagina: int,
    por_pagina: int,
    somente_recebiveis: bool,
    solicitacao_provider: SolicitacaoProviderInterface,
    recebimento_provider: RecebimentoProviderInterface,
    filtros: Optional[Dict[str, Optional[str]]] = None,
    ordenar_por: Optional[str] = None,
    direcao: str = "asc",
) -> Dict[str, Any]:
    """
    Monta uma página da lista inicial, com a situação de cada solicitação.

    Os filtros por coluna e a ordenação são aplicados no provider, antes da paginação, para
    valerem sobre todas as solicitações e não só sobre a página visível.
    """
    bancadas = await recebimento_provider.listar_bancadas()
    status_item = await recebimento_provider.listar_status_item()
    codigos_status = (
        [codigo for codigo, dados in status_item.items() if dados["permite_recebimento"]]
        if somente_recebiveis
        else None
    )
    # O filtro de bancada vira os códigos de laboratório daquela bancada (vazio se ela não existir).
    filtros_por_coluna = {
        coluna: valor.strip() for coluna, valor in (filtros or {}).items() if valor and valor.strip()
    }
    bancada_filtrada = filtros_por_coluna.pop("bancada", None)
    codigos_lab_filtro = (
        None
        if bancada_filtrada is None
        else [
            codigo
            for codigo, dados in bancadas.items()
            if dados["bancada"] == bancada_filtrada.upper()
        ]
    )
    consulta = {
        "filtros": filtros_por_coluna,
        "codigos_lab_filtro": codigos_lab_filtro,
        "ordenar_por": ordenar_por,
        "direcao": direcao,
    }
    # A prioridade da fila é decidida antes da paginação: solicitações com CO ainda não recebido
    # vêm primeiro. Quando o usuário escolhe uma ordenação, ela vale no lugar da prioridade.
    # Os argumentos extras vão por posição, como os demais.
    codigos_lab_urgentes: List[str] = []
    ja_recebidas: List[str] = []
    if not ordenar_por:
        codigos_lab_urgentes = [
            codigo for codigo, dados in bancadas.items() if dados["bancada"] == BANCADA_CO
        ]
        ja_recebidas = await recebimento_provider.listar_codigos_com_exame_recebido(BANCADA_CO)
    resultado = await solicitacao_provider.listar_solicitacoes(
        pagina,
        por_pagina,
        codigos_status,
        list(bancadas),
        codigos_lab_urgentes,
        ja_recebidas,
        consulta,
    )
    
    exames_por_codigo: Dict[str, List[Dict[str, Any]]] = {}
    for exame in await recebimento_provider.listar_exames_das_solicitacoes(
        [solicitacao["codigo"] for solicitacao in resultado["solicitacoes"]]
    ):
        exames_por_codigo.setdefault(exame["codigo_solicitacao"], []).append(exame)

    hoje = _agora().astimezone(FUSO_HOSPITAL).date()
    return {
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total": resultado["total"],
        "total_paginas": ceil(resultado["total"] / por_pagina),
        "solicitacoes": [
            _resumo_para_lista(
                solicitacao,
                exames_por_codigo.get(solicitacao["codigo"], []),
                bancadas,
                status_item,
                hoje,
            )
            for solicitacao in resultado["solicitacoes"]
        ],
    }


def _exame_detalhado(exame: Dict[str, Any]) -> Dict[str, Any]:
    """Formata para os detalhes um exame com tudo o que foi gravado sobre ele."""
    return {
        **_exame_para_resposta(exame),
        "quantidade_pecas": exame["quantidade_pecas"],
        "procedimento": exame["procedimento"],
        "referencia_hp": exame["referencia_hp"],
        "amostras": [
            {
                **amostra,
                "conferencia": (
                    {
                        "conferido_por": amostra["conferencia"]["conferido_por"],
                        "conferido_em": _formatar_momento(amostra["conferencia"]["conferido_em"]),
                    }
                    if amostra["conferencia"]
                    else None
                ),
            }
            for amostra in exame["amostras"]
        ],
        "nao_conformidades": [
            {
                **registro,
                "registrado_em": _formatar_momento(registro["registrado_em"]),
                "resolvida_em": (
                    _formatar_momento(registro["resolvida_em"]) if registro["resolvida_em"] else None
                ),
            }
            for registro in exame["nao_conformidades"]
        ],
    }


async def obter_solicitacao(
    codigo: str,
    solicitacao_provider: SolicitacaoProviderInterface,
    recebimento_provider: RecebimentoProviderInterface,
) -> Dict[str, Any]:
    """Monta a tela de conferência: paciente, clínica e amostras das bancadas."""
    solicitacao, numero_amostra_lida = await _resolver_solicitacao(codigo, solicitacao_provider)
    itens = await _exigir_itens_das_bancadas(solicitacao, recebimento_provider)
    status_item = await recebimento_provider.listar_status_item()
    exames = await recebimento_provider.listar_historico_da_solicitacao(solicitacao["codigo"])
    recebidos = _numero_recebido_por_tipo(exames)
    gravadas = {
        amostra["numero_amostra"]: amostra
        for exame in exames
        if exame["status"] == STATUS_RECEBIDO
        for amostra in exame["amostras"]
    }

    amostras = []
    for item in itens:
        gravada = gravadas.get(item["numero_amostra"])
        conferencia = gravada["conferencia"] if gravada else None
        if item["bancada"] in recebidos:
            motivo_bloqueio = f"Exame {recebidos[item['bancada']]} já recebido."
        else:
            motivo_bloqueio = _motivo_de_bloqueio(item, solicitacao, status_item)
        amostras.append(
            {
                "numero_amostra": item["numero_amostra"],
                "bancada": item["bancada"],
                "codigo_lab": item["codigo_lab"],
                "sigla_exame": item["sigla_exame"],
                "nome_exame": item["nome_exame"],
                "descricao_material": item["descricao_material"],
                "exige_descricao": not item["descricao_material"],
                "cod_status_item": item["cod_status_item"],
                "status_item_exame": item["status_item_exame"],
                "recebivel": motivo_bloqueio is None,
                "motivo_bloqueio": motivo_bloqueio,
                "recebida": bool(gravada and gravada["recebida"]),
                "material_informado": gravada["descricao_informada"] if gravada else None,
                "conferencia": (
                    {
                        "conferido_por": conferencia["conferido_por"],
                        "conferido_em": _formatar_momento(conferencia["conferido_em"]),
                    }
                    if conferencia
                    else None
                ),
            }
        )

    recebiveis = sum(amostra["recebivel"] for amostra in amostras)
    hoje = _agora().astimezone(FUSO_HOSPITAL).date()
    return {
        "codigo": solicitacao["codigo"],
        "situacao": _situacao_na_lista(recebiveis, recebidos, exames),
        "urgente": _solicitacao_urgente(exames, itens),
        "numero_amostra_lida": numero_amostra_lida,
        "data_solicitacao": solicitacao["data_solicitacao"],
        "paciente": {
            "nome": solicitacao["nome_paciente"],
            "prontuario": solicitacao["prontuario"],
            "data_nascimento": solicitacao["data_nascimento"],
            "idade": _calcular_idade(solicitacao["data_nascimento"], hoje),
        },
        "origem": solicitacao["origem"],
        "especialidade": solicitacao["especialidade"],
        "convenio": solicitacao["convenio"],
        "unidade": solicitacao["unidade"],
        "informacoes_clinica": solicitacao["informacoes_clinica"],
        "amostras": amostras,
        "exames": [_exame_detalhado(exame) for exame in exames],
    }

def _falha_de_recebimento(
    tipo: str,
    itens: List[Dict[str, Any]],
    marcadas: Dict[int, Dict[str, Any]],
    codigo_http: int,
    detalhe: str,
) -> Dict[str, Any]:
    """Monta o registro de um exame da bancada que não foi gravado, com as amostras afetadas."""
    return {
        "tipo": tipo,
        "amostras": sorted(
            item["numero_amostra"]
            for item in itens
            if item["bancada"] == tipo and item["numero_amostra"] in marcadas
        ),
        "codigo_http": codigo_http,
        "detail": detalhe,
    }


async def _gravar_exame_isolado(
    dados_exame: Dict[str, Any],
    usuario: str,
    momento: datetime,
    recebimento_provider: RecebimentoProviderInterface,
) -> Tuple[Optional[Dict[str, Any]], Optional[Tuple[int, str]]]:
    """
    Grava um único exame em transação própria.

    Retorna (exame gravado, None) em caso de sucesso ou (None, (código HTTP, mensagem)) em caso
    de falha, para que o erro de um exame não impeça a gravação dos demais.
    """
    try:
        gravados = await recebimento_provider.registrar_recebimento([dados_exame], usuario, momento)
        return gravados[0], None
    except HTTPException as erro:
        return None, (erro.status_code, str(erro.detail))
    except Exception:
        logger.exception(
            "Falha inesperada ao gravar o exame %s da solicitação %s.",
            dados_exame["tipo"],
            dados_exame["codigo_solicitacao"],
        )
        return None, (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Erro interno ao gravar o exame {dados_exame['tipo']}. Nada foi gravado para ele.",
        )

def _validar_marcacoes(
    marcacoes: List[Dict[str, Any]],
    itens: List[Dict[str, Any]],
    solicitacao: Dict[str, Any],
    status_item: Dict[str, Dict[str, Any]],
) -> Dict[int, Dict[str, Any]]:
    """Valida as amostras enviadas e retorna as marcadas para recebimento, por número."""
    numeros = [marcacao["numero_amostra"] for marcacao in marcacoes]
    if len(numeros) != len(set(numeros)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A mesma amostra foi enviada mais de uma vez.",
        )

    itens_por_numero = {item["numero_amostra"]: item for item in itens}
    marcadas: Dict[int, Dict[str, Any]] = {}
    for marcacao in marcacoes:
        numero = marcacao["numero_amostra"]
        item = itens_por_numero.get(numero)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"A amostra {numero} não pertence às bancadas desta solicitação.",
            )
        if not marcacao["receber"]:
            continue
        motivo_bloqueio = _motivo_de_bloqueio(item, solicitacao, status_item)
        if motivo_bloqueio:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Amostra {numero}: {motivo_bloqueio}",
            )
        if not item["descricao_material"] and not (marcacao.get("descricao_informada") or "").strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"A amostra {numero} está sem descrição no AGHU. Informe o material do frasco.",
            )
        marcadas[numero] = marcacao

    if not marcadas:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Marque ao menos uma amostra para receber.",
        )
    return marcadas


def _validar_checklist(checklist: Dict[str, bool]) -> None:
    """Exige os três itens do checklist, que vale para todo o recebimento (RF004)."""
    if not all(checklist[campo] for campo in ITENS_CHECKLIST):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Conclua o checklist do recebimento antes de receber.",
        )


async def _validar_dados_hp(
    dados_hp: Optional[Dict[str, Any]], recebimento_provider: RecebimentoProviderInterface
) -> Dict[str, Any]:
    """Exige os dados de HP e confere o procedimento; respostas 422 não consomem número."""
    if dados_hp is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Informe a quantidade de peças, a urgência e o procedimento do HP.",
        )
    if await recebimento_provider.obter_procedimento_hp(dados_hp["procedimento_id"]) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Selecione um procedimento de HP válido.",
        )
    return dados_hp


def _validar_referencia_hp(referencia_hp: Optional[str]) -> Optional[str]:
    """Confere o formato da referência da IHQ ao HP de origem, que é opcional."""
    limpa = (referencia_hp or "").strip()
    if not limpa:
        return None
    if not PADRAO_REFERENCIA_HP.match(limpa):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Informe a referência do HP no formato HP-AAAA/N.",
        )
    return limpa


def _dados_comuns_do_exame(
    tipo: str, ano: int, solicitacao: Dict[str, Any]
) -> Dict[str, Any]:
    """Monta os dados do exame copiados da solicitação do AGHU. O nome não é gravado."""
    return {
        "tipo": tipo,
        "ano": ano,
        "codigo_solicitacao": solicitacao["codigo"],
        "prontuario": solicitacao["prontuario"],
        "origem": solicitacao["origem"],
        "especialidade": solicitacao["especialidade"],
        "unidade": solicitacao["unidade"],
    }


def _dados_da_amostra(
    item: Dict[str, Any],
    marcacao: Optional[Dict[str, Any]],
    checklist: Optional[Dict[str, bool]] = None,
) -> Dict[str, Any]:
    """
    Monta a amostra com os dados relidos do AGHU; do cliente vêm só as marcações.

    O checklist é único, e cada amostra recebida guarda o resultado na própria conferência.
    """
    informada = (marcacao.get("descricao_informada") or "").strip() if marcacao else ""
    return {
        "numero_amostra": item["numero_amostra"],
        "bancada": item["bancada"],
        "sigla_exame": item["sigla_exame"],
        "nome_exame": item["nome_exame"],
        "descricao_material": item["descricao_material"],
        "descricao_informada": informada if not item["descricao_material"] and informada else None,
        "cod_status_item": item["cod_status_item"],
        "recebida": marcacao is not None,
        "conferencia": dict(checklist) if marcacao and checklist else None,
    }


async def receber_amostras(
    codigo: str,
    marcacoes: List[Dict[str, Any]],
    checklist: Dict[str, bool],
    dados_hp: Optional[Dict[str, Any]],
    referencia_hp: Optional[str],
    usuario: str,
    ip_origem: Optional[str],
    solicitacao_provider: SolicitacaoProviderInterface,
    recebimento_provider: RecebimentoProviderInterface,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Conclui o recebimento: um exame por bancada, com nº interno gerado em transação."""
    solicitacao, _ = await _resolver_solicitacao(codigo, solicitacao_provider)
    itens = await _exigir_itens_das_bancadas(solicitacao, recebimento_provider)
    status_item = await recebimento_provider.listar_status_item()
    marcadas = _validar_marcacoes(marcacoes, itens, solicitacao, status_item)
    _validar_checklist(checklist)

    tipos = sorted({item["bancada"] for item in itens if item["numero_amostra"] in marcadas})
    existentes = await recebimento_provider.listar_exames_da_solicitacao(solicitacao["codigo"])
    recebidos = _numero_recebido_por_tipo(existentes)
    falhas: List[Dict[str, Any]] = []
    for tipo in tipos:
        if tipo in recebidos:
            falhas.append(
                _falha_de_recebimento(
                    tipo,
                    itens,
                    marcadas,
                    status.HTTP_409_CONFLICT,
                    f"Solicitação já recebida: {recebidos[tipo]}.",
                )
            )
    tipos = [tipo for tipo in tipos if tipo not in recebidos]
    if not tipos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Solicitação já recebida: {', '.join(recebidos[f['tipo']] for f in falhas)}.",
        )

    dados_hp_validos = (
        await _validar_dados_hp(dados_hp, recebimento_provider) if BANCADA_HP in tipos else None
    )
    referencia_valida = _validar_referencia_hp(referencia_hp) if BANCADA_IHQ in tipos else None

    momento = _agora()
    ano = _ano_do_hospital(momento)
    dados_exames = []
    for tipo in tipos:
        itens_do_tipo = [item for item in itens if item["bancada"] == tipo]
        dados_exame = {
            **_dados_comuns_do_exame(tipo, ano, solicitacao),
            "prefixo": itens_do_tipo[0]["prefixo"],
            "amostras": [
                _dados_da_amostra(item, marcadas.get(item["numero_amostra"]), checklist)
                for item in itens_do_tipo
            ],
        }
        if tipo == BANCADA_HP:
            dados_exame.update(dados_hp_validos)
        elif tipo == BANCADA_CO:
            dados_exame["urgente"] = True  # CARE-RF007: a congelação já entra como urgente.
        elif tipo == BANCADA_IHQ:
            dados_exame["referencia_hp"] = referencia_valida
        dados_exames.append(dados_exame)

    # Cada exame é gravado em transação própria: uma falha não desfaz nem impede os demais.
    gravados_com_dados: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    for dados_exame in dados_exames:
        gravado, erro = await _gravar_exame_isolado(
            dados_exame, usuario, momento, recebimento_provider
        )
        if gravado is not None:
            gravados_com_dados.append((gravado, dados_exame))
        elif erro is not None:
            falhas.append(
                _falha_de_recebimento(dados_exame["tipo"], itens, marcadas, erro[0], erro[1])
            )

    if not gravados_com_dados:
        # Nada foi gravado: mantém o comportamento anterior, com o erro HTTP do primeiro exame.
        raise HTTPException(
            status_code=falhas[0]["codigo_http"],
            detail="; ".join(falha["detail"] for falha in falhas),
        )

    # A auditoria faz commit próprio, por isso só roda depois da transação de negócio.
    status_anterior = _status_anterior_por_tipo(existentes)
    for exame, dados_exame in gravados_com_dados:
        resolvidas = exame["nao_conformidades_resolvidas"]
        anteriores: Dict[str, Any] = {"status": status_anterior.get(exame["tipo"])}
        if resolvidas:
            anteriores["nao_conformidades_pendentes"] = resolvidas
        await registrar_auditoria(
            db=db,
            usuario=usuario,
            categoria=CATEGORIA_AUDITORIA,
            acao="RECEBER_AMOSTRA",
            recurso=f"exame:{exame['id']}",
            dados_anteriores=anteriores,
            dados_novos={
                "status": exame["status"],
                "numero_interno": exame["numero_interno"],
                "tipo": exame["tipo"],
                "codigo_solicitacao": exame["codigo_solicitacao"],
                "quantidade_pecas": dados_exame.get("quantidade_pecas"),
                "urgente": dados_exame.get("urgente"),
                "procedimento_id": dados_exame.get("procedimento_id"),
                "referencia_hp": dados_exame.get("referencia_hp"),
                "checklist": checklist,
                "amostras_recebidas": [
                    amostra["numero_amostra"] for amostra in exame["amostras"] if amostra["recebida"]
                ],
                "nao_conformidades_resolvidas": resolvidas,
            },
            ip_origem=ip_origem,
        )

    return {
        "codigo": solicitacao["codigo"],
        "exames": [_exame_para_resposta(exame) for exame, _ in gravados_com_dados],
        "falhas": sorted(falhas, key=lambda falha: falha["tipo"]),
    }


async def registrar_nao_conformidade(
    codigo: str,
    motivo_id: int,
    observacao: str,
    numero_cmce: Optional[str],
    medico_solicitante: Optional[str],
    usuario: str,
    ip_origem: Optional[str],
    solicitacao_provider: SolicitacaoProviderInterface,
    recebimento_provider: RecebimentoProviderInterface,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Devolve à origem as bancadas ainda não recebidas, sem consumir nº interno.

    Vale para qualquer status do AGHU, para que um frasco que chegou indevidamente
    (ex.: item cancelado) possa ser devolvido com registro.
    """
    solicitacao, _ = await _resolver_solicitacao(codigo, solicitacao_provider)
    itens = await _exigir_itens_das_bancadas(solicitacao, recebimento_provider)

    motivo = await recebimento_provider.obter_motivo(motivo_id)
    if motivo is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Selecione um motivo de não conformidade válido.",
        )

    observacao_limpa = observacao.strip()
    if not observacao_limpa:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Informe a observação da não conformidade.",
        )
    numero_cmce_limpo = (numero_cmce or "").strip() or None
    medico_limpo = (medico_solicitante or "").strip() or None

    existentes = await recebimento_provider.listar_exames_da_solicitacao(solicitacao["codigo"])
    recebidos = _numero_recebido_por_tipo(existentes)
    tipos = sorted({item["bancada"] for item in itens} - set(recebidos))
    if not tipos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Solicitação já recebida: {', '.join(recebidos.values())}.",
        )

    momento = _agora()
    ano = _ano_do_hospital(momento)
    dados_exames = [
        {
            **_dados_comuns_do_exame(tipo, ano, solicitacao),
            "amostras": [
                _dados_da_amostra(item, None) for item in itens if item["bancada"] == tipo
            ],
        }
        for tipo in tipos
    ]

    gravados = await recebimento_provider.registrar_nao_conformidade(
        dados_exames,
        {
            "motivo_id": motivo_id,
            "observacao": observacao_limpa,
            "numero_cmce": numero_cmce_limpo,
            "medico_solicitante": medico_limpo,
        },
        usuario,
        momento,
    )

    # A auditoria faz commit próprio, por isso só roda depois da transação de negócio.
    status_anterior = _status_anterior_por_tipo(existentes)
    for exame in gravados:
        await registrar_auditoria(
            db=db,
            usuario=usuario,
            categoria=CATEGORIA_AUDITORIA,
            acao="REGISTRAR_NAO_CONFORMIDADE",
            recurso=f"exame:{exame['id']}",
            dados_anteriores={"status": status_anterior.get(exame["tipo"])},
            dados_novos={
                "status": STATUS_DEVOLVIDO,
                "tipo": exame["tipo"],
                "codigo_solicitacao": exame["codigo_solicitacao"],
                "motivo": motivo["descricao"],
                "observacao": observacao_limpa,
                "numero_cmce": numero_cmce_limpo,
                "medico_solicitante": medico_limpo,
            },
            ip_origem=ip_origem,
        )

    return {
        "codigo": solicitacao["codigo"],
        "motivo": motivo["descricao"],
        "observacao": observacao_limpa,
        "exames": [_exame_para_resposta(exame) for exame in gravados],
    }
