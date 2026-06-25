from fastapi import APIRouter, Depends
from typing import List
from ..auth.auth import auth_handler

router = APIRouter(
    prefix="/api/aih",
    tags=["AIH"],
    dependencies=[Depends(auth_handler.decode_token)]
)

@router.get("", response_model=List[dict])
async def listar_aihs():
    """Exemplo de listagem de AIHs."""
    return [
        {"numero": "1234567890", "paciente": "Paciente Exemplo A", "data_internacao": "2024-05-01"},
        {"numero": "0987654321", "paciente": "Paciente Exemplo B", "data_internacao": "2024-05-02"}
    ]
