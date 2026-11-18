from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List

from ..auth.auth import auth_handler
from ..auth.authorization import Permissao, exigir_permissao

router = APIRouter(prefix="/api", tags=["Admin"], dependencies=[Depends(auth_handler.decode_token)])

class AdminData(BaseModel):
    message: str
    user_groups: List[str]

async def verify_admin_group(current_user: dict = Depends(exigir_permissao(Permissao.SEGURANCA_GERENCIAR))):
    """Mantém nome legado da dependência, agora baseado em permissão local."""
    return current_user

@router.get("/admin-only-data", response_model=AdminData)
async def get_admin_data(current_user: dict = Depends(verify_admin_group)):
    """
    Returns data only accessible by users with admin privileges.
    """
    return AdminData(
        message="This is highly confidential admin data!",
        user_groups=current_user.get("groups", [])
    )

class ADUserSearchResponse(BaseModel):
    exists: bool
    username: str
    displayName: str
    email: str
    department: str

@router.get("/admin/ad-user-search/{username}", response_model=ADUserSearchResponse)
async def search_ad_user(username: str, current_user: dict = Depends(verify_admin_group)):
    """
    Busca e valida um usuário no Active Directory (ou Mock) pelo login de rede.
    Restrito a administradores do sistema.
    """
    res = auth_handler.search_ad_user(username)
    return ADUserSearchResponse(**res)
