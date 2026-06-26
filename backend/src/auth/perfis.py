"""
Controle de acesso por perfil (RBAC) — scaffold.

O mapeamento definitivo de grupos do AD para os 5 perfis operacionais depende
de definição com o time do HC (sinalizado em aberto no README do frontend).
Por isso, por enquanto:

  - O grupo de administrador já conhecido (GLO-SEC-HCPE-SETISD) -> perfil Admin,
    que acessa tudo.
  - Demais perfis ainda não têm grupos AD mapeados. Enquanto `MODO_PERMISSIVO`
    estiver ligado, qualquer usuário autenticado acessa as rotas operacionais
    (mas rotas exclusivas de Admin continuam protegidas).

Quando o HC definir os grupos, basta preencher `GRUPO_AD_PARA_PERFIL` e desligar
`MODO_PERMISSIVO`. Segue o mesmo padrão de `verify_admin_group`
(src/routers/admin.py).
"""

from fastapi import Depends, HTTPException, status

from .auth import auth_handler


class Perfil:
    ADMIN = "Admin"
    RECEPCIONISTA = "Recepcionista"
    MACROSCOPISTA = "Macroscopista"
    TECNICO = "Técnico de Laboratório"
    RESIDENTE = "Residente"
    PATOLOGISTA = "Médico Patologista"


GRUPO_ADMIN = "GLO-SEC-HCPE-SETISD"

# Mapeamento grupo AD -> perfil. TODO(HC): completar com os grupos reais.
GRUPO_AD_PARA_PERFIL: dict[str, str] = {
    GRUPO_ADMIN: Perfil.ADMIN,
}

# Enquanto o mapeamento de perfis não está definido pelo HC, libera usuários
# autenticados nas rotas operacionais. Trocar para False quando completo.
MODO_PERMISSIVO = True


def is_admin(current_user: dict) -> bool:
    return GRUPO_ADMIN in (current_user.get("groups", []) or [])


def perfis_do_usuario(current_user: dict) -> set[str]:
    grupos = current_user.get("groups", []) or []
    return {GRUPO_AD_PARA_PERFIL[g] for g in grupos if g in GRUPO_AD_PARA_PERFIL}


def require_perfil(*perfis_exigidos: str):
    """
    Dependency factory: exige que o usuário tenha pelo menos um dos perfis.
    Admin sempre passa. Em MODO_PERMISSIVO, usuários autenticados passam mesmo
    sem perfil mapeado (transição até o HC definir os grupos).
    """

    async def _verificar(
        current_user: dict = Depends(auth_handler.decode_token),
    ) -> dict:
        if is_admin(current_user):
            return current_user

        if perfis_exigidos and perfis_do_usuario(current_user).intersection(
            perfis_exigidos
        ):
            return current_user

        if MODO_PERMISSIVO:
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil não tem permissão para esta operação.",
        )

    return _verificar
