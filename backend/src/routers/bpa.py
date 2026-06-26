from fastapi import APIRouter, Depends
from typing import List
from ..auth.auth import auth_handler

router = APIRouter(
    prefix="/api/bpa",
    tags=["BPA"],
    dependencies=[Depends(auth_handler.decode_token)]
)

@router.get("", response_model=List[dict])
async def listar_bpas():
    """Exemplo de listagem de BPAs."""
    return [
        {"procedimento": "0301010072", "descricao": "CONSULTA MEDICA EM ATENCAO ESPECIALIZADA", "quantidade": 10},
        {"procedimento": "0301010048", "descricao": "CONSULTA DE PRE-NATAL", "quantidade": 5}
    ]
