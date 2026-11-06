"""Interpretação do código lido na etiqueta do AGHU ou digitado na Recepção."""
import re
from typing import Optional, Tuple

# O código da solicitação tem 6 ou 7 dígitos, e o número da amostra vem de três formas.
_SO_CODIGO = re.compile(r"^(\d{6,7})$")
_CODIGO_E_AMOSTRA_EM_3_DIGITOS = re.compile(r"^(\d{6,7})(\d{3})$")
_CODIGO_HIFEN_AMOSTRA = re.compile(r"^(\d{6,7})-(\d{1,3})$")


def interpretar_codigo_lido(texto: str) -> Optional[Tuple[str, Optional[int]]]:
    """
    Separa o código da solicitação e o número da amostra.

    Aceita `CODIGO`, `CODIGO` + 3 dígitos da amostra e `CODIGO-N`. Retorna None em qualquer
    outro formato ou com amostra zero. Oito dígitos são recusados por serem ambíguos e por
    terem o tamanho do prontuário, que pode ser bipado por engano.
    """
    limpo = texto.strip()

    so_codigo = _SO_CODIGO.match(limpo)
    if so_codigo:
        return so_codigo.group(1), None

    com_amostra = _CODIGO_E_AMOSTRA_EM_3_DIGITOS.match(limpo) or _CODIGO_HIFEN_AMOSTRA.match(limpo)
    if com_amostra and int(com_amostra.group(2)) >= 1:
        return com_amostra.group(1), int(com_amostra.group(2))

    return None
