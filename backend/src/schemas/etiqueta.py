from pydantic import BaseModel


class EtiquetaOut(BaseModel):
    """
    Payload de etiqueta de um subproduto.

    Contém tudo que será impresso quando a impressora térmica chegar; por
    enquanto serve para exibição/conferência na tela. `qr_code` é a string que
    a impressora renderizará como imagem de QR Code.
    """

    tipo: str  # FRASCO | CASSETE | BLOCO | LAMINA
    numero_solicitacao: str
    codigo: str  # codigo_interno (frasco) ou letra_fragmento (cassete)
    qr_code: str
