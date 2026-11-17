from datetime import date
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, Query

from ..controllers import solicitacao_controller
from ..dependencies import get_solicitacao_provider
from ..providers.interfaces.solicitacao_provider_interface import SolicitacaoProviderInterface

from ..auth.auth import auth_handler

# --- PONTO ÚNICO DE CONFIGURAÇÃO PARA ESTE ROTEADOR ---
STRATEGY = "csv"
# ----------------------------------------------------

router = APIRouter(
    prefix="/api/solicitacoes",
    tags=["Solicitações"],
    dependencies=[Depends(auth_handler.decode_token)]
)


@router.get("", response_model=List[dict])
async def listar_solicitacoes(
    limite: int = Query(100, ge=1, le=1000, description="Máximo de solicitações distintas retornadas (todas as amostras de cada uma)"),
    data_inicio: Optional[date] = Query(None, description="Data inicial da solicitação (AAAA-MM-DD)"),
    data_fim: Optional[date] = Query(None, description="Data final da solicitação (AAAA-MM-DD)"),
    tipo: Optional[Literal["HP", "CG", "CCV", "CO", "IHQ"]] = Query(None, description="Tipo de exame sugerido"),
    provider: SolicitacaoProviderInterface = Depends(get_solicitacao_provider(STRATEGY)),
):
    """Lista itens de exame de AP do AGHU, mais recentes primeiro."""
    return await solicitacao_controller.listar_solicitacoes(
        provider, limite=limite, data_inicio=data_inicio, data_fim=data_fim, tipo=tipo
    )


@router.get("/{codigo}", response_model=List[dict])
async def obter_solicitacao(
    codigo: str,
    provider: SolicitacaoProviderInterface = Depends(get_solicitacao_provider(STRATEGY)),
):
    """Retorna os itens de AP de uma solicitação do AGHU.

    Aceita o código da solicitação (todas as amostras) ou o id composto
    `<codigoSolicitacao>-<numeroAmostra>` (apenas aquela amostra).
    """
    return await solicitacao_controller.obter_solicitacao(codigo, provider)
