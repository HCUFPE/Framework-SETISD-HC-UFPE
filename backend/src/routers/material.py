from fastapi import APIRouter, Depends
from typing import List
from ..auth.auth import auth_handler

router = APIRouter(
    prefix="/api/material",
    tags=["Material"],
    dependencies=[Depends(auth_handler.decode_token)]
)

@router.get("/estoque", response_model=List[dict])
async def consultar_estoque():
    """Exemplo de consulta de estoque de materiais."""
    return [
        {"codigo": 101, "nome": "Seringa 10ml", "estoque": 500},
        {"codigo": 102, "nome": "Agulha 25x7", "estoque": 1200}
    ]
