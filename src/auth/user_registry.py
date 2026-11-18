"""Provisiona identidades e perfis locais exclusivamente para o adapter mock."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .authorization import Perfil as PerfilCodigo, USUARIOS_MOCK
from ..models.usuario_perfil import Perfil as PerfilModel
from ..models.usuario_perfil import Usuario, UsuarioPerfil


async def seed_mock_authorization(db: AsyncSession) -> None:
    """Cria cadastro local inicial de desenvolvimento sem sobrescrever alterações locais."""
    perfis: dict[str, PerfilModel] = {}
    for perfil_codigo in PerfilCodigo:
        result = await db.execute(
            select(PerfilModel).where(PerfilModel.codigo == perfil_codigo.value)
        )
        perfil = result.scalar_one_or_none()
        if perfil is None:
            perfil = PerfilModel(codigo=perfil_codigo.value, nome=perfil_codigo.value.replace("_", " "))
            db.add(perfil)
        perfis[perfil_codigo.value] = perfil
    await db.flush()

    for identidade in USUARIOS_MOCK.values():
        login = identidade.username.strip().lower()
        result = await db.execute(
            select(Usuario).where(Usuario.login_institucional == login)
        )
        usuario = result.scalar_one_or_none()
        if usuario is not None:
            continue

        usuario = Usuario(login_institucional=login, nome=identidade.nome, ativo=True)
        db.add(usuario)
        await db.flush()
        for codigo in identidade.perfis:
            perfil = perfis.get(codigo)
            if perfil is not None:
                db.add(UsuarioPerfil(usuario_id=usuario.id, perfil_id=perfil.id))

    await db.commit()
