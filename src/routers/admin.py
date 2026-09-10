from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List

from ..auth.auth import auth_handler

router = APIRouter(prefix="/api", tags=["Admin"])

class AdminData(BaseModel):
    message: str
    user_groups: List[str]

async def verify_admin_group(current_user: dict = Depends(auth_handler.decode_token)):
    ADMIN_GROUP = "GLO-SEC-HCPE-SETISD"
    if ADMIN_GROUP not in current_user.get("groups", []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")
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
