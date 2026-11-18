"""Catálogo local de perfis e dependências de autorização do Sistema AP."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import auth_handler
from ..models.usuario_perfil import Perfil as PerfilModel
from ..models.usuario_perfil import Usuario, UsuarioPerfil
from ..resources.database import get_app_db_session


class Perfil(StrEnum):
    RECEPCIONISTA = "RECEPCIONISTA"
    PROFISSIONAL_MACROSCOPIA = "PROFISSIONAL_MACROSCOPIA"
    TECNICO_PROCESSAMENTO = "TECNICO_PROCESSAMENTO"
    TECNICO_IHQ = "TECNICO_IHQ"
    MEDICO_RESIDENTE = "MEDICO_RESIDENTE"
    PATOLOGISTA_PRECEPTOR = "PATOLOGISTA_PRECEPTOR"
    CITOTECNICO = "CITOTECNICO"
    TECNICO_ARQUIVO = "TECNICO_ARQUIVO"
    COORDENACAO_ADMINISTRADOR = "COORDENACAO_ADMINISTRADOR"


class Permissao(StrEnum):
    CASOS_CONSULTAR = "casos:consultar"
    RECEPCAO_RECEBER = "recepcao:receber"
    RECEPCAO_REGISTRAR_NAO_CONFORMIDADE = "recepcao:registrar_nao_conformidade"
    RECEPCAO_ACIONAR_PLANTAO = "recepcao:acionar_plantao"
    CASOS_CANCELAR = "casos:cancelar"
    DEVOLUCOES_CONSULTAR = "devolucoes:consultar"
    DEVOLUCOES_ALTERAR_SITUACAO = "devolucoes:alterar_situacao"
    SEGURANCA_GERENCIAR = "seguranca:gerenciar"
    AUDITORIA_CONSULTAR = "auditoria:consultar"


# Atribuições de UC003/UC028, UC005-UC007, UC009, UC025-UC027 e UC033-UC034
# de docs/especificacao/03-casos-uso.md. Células sem associação explícita ficam negadas.
PERMISSOES_POR_PERFIL: dict[Perfil, frozenset[Permissao]] = {
    Perfil.RECEPCIONISTA: frozenset({Permissao.CASOS_CONSULTAR, Permissao.RECEPCAO_RECEBER,
                                    Permissao.RECEPCAO_REGISTRAR_NAO_CONFORMIDADE,
                                    Permissao.RECEPCAO_ACIONAR_PLANTAO,
                                    Permissao.DEVOLUCOES_CONSULTAR,
                                    Permissao.DEVOLUCOES_ALTERAR_SITUACAO}),
    Perfil.PROFISSIONAL_MACROSCOPIA: frozenset({Permissao.CASOS_CONSULTAR,
                                                Permissao.RECEPCAO_REGISTRAR_NAO_CONFORMIDADE,
                                                Permissao.RECEPCAO_ACIONAR_PLANTAO}),
    Perfil.TECNICO_PROCESSAMENTO: frozenset({Permissao.CASOS_CONSULTAR,
                                             Permissao.RECEPCAO_REGISTRAR_NAO_CONFORMIDADE,
                                             Permissao.RECEPCAO_ACIONAR_PLANTAO}),
    Perfil.TECNICO_IHQ: frozenset({Permissao.CASOS_CONSULTAR,
                                   Permissao.RECEPCAO_REGISTRAR_NAO_CONFORMIDADE,
                                   Permissao.RECEPCAO_ACIONAR_PLANTAO}),
    Perfil.MEDICO_RESIDENTE: frozenset({Permissao.CASOS_CONSULTAR,
                                        Permissao.RECEPCAO_REGISTRAR_NAO_CONFORMIDADE,
                                        Permissao.RECEPCAO_ACIONAR_PLANTAO}),
    Perfil.PATOLOGISTA_PRECEPTOR: frozenset({Permissao.CASOS_CONSULTAR,
                                             Permissao.RECEPCAO_REGISTRAR_NAO_CONFORMIDADE,
                                             Permissao.RECEPCAO_ACIONAR_PLANTAO}),
    # UC013/UC020 mencionam Citotécnico em processos futuros, mas as permissões
    # específicas continuam pendentes de validação SAP; somente consulta (UC003/028).
    Perfil.CITOTECNICO: frozenset({Permissao.CASOS_CONSULTAR}),
    Perfil.TECNICO_ARQUIVO: frozenset({Permissao.CASOS_CONSULTAR}),
    Perfil.COORDENACAO_ADMINISTRADOR: frozenset({Permissao.CASOS_CONSULTAR,
                                                  Permissao.RECEPCAO_ACIONAR_PLANTAO,
                                                  Permissao.CASOS_CANCELAR,
                                                  Permissao.DEVOLUCOES_CONSULTAR,
                                                  Permissao.DEVOLUCOES_ALTERAR_SITUACAO,
                                                  Permissao.SEGURANCA_GERENCIAR,
                                                  Permissao.AUDITORIA_CONSULTAR}),
}


def resolver_permissoes(perfis: list[str]) -> list[str]:
    """Retorna a união das permissões concedidas pelos perfis conhecidos."""
    permissoes: set[Permissao] = set()
    for nome in perfis:
        try:
            permissoes.update(PERMISSOES_POR_PERFIL[Perfil(nome)])
        except (ValueError, KeyError):
            continue
    return sorted(permissao.value for permissao in permissoes)


async def listar_perfis_locais(login: str, db: AsyncSession) -> list[str]:
    """Carrega apenas perfis ativos de um usuário previamente habilitado no banco local."""
    login_normalizado = login.strip().lower()
    resultado_usuario = await db.execute(
        select(Usuario).where(Usuario.login_institucional == login_normalizado)
    )
    usuario = resultado_usuario.scalar_one_or_none()
    if usuario is None or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não cadastrado ou inativo para este sistema",
        )

    resultado_perfis = await db.execute(
        select(PerfilModel.codigo)
        .join(UsuarioPerfil, UsuarioPerfil.perfil_id == PerfilModel.id)
        .where(UsuarioPerfil.usuario_id == usuario.id, PerfilModel.ativo.is_(True))
        .order_by(PerfilModel.codigo)
    )
    return list(resultado_perfis.scalars().all())


async def identidade_com_permissoes_locais(
    identidade: dict, db: AsyncSession
) -> dict:
    """Combina atributos autenticados pelo provedor com perfis persistidos localmente."""
    login = identidade.get("username") or identidade.get("sub")
    if not isinstance(login, str) or not login.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identidade inválida")
    perfis = await listar_perfis_locais(login, db)
    identidade_local = dict(identidade)
    identidade_local["profiles"] = perfis
    identidade_local["permissions"] = resolver_permissoes(perfis)
    return identidade_local


def exigir_permissao(permissao: Permissao) -> Callable[..., dict]:
    """Cria dependência que exige uma permissão explícita na identidade autenticada."""
    async def verificar(
        usuario: dict = Depends(auth_handler.decode_token),
        db: AsyncSession = Depends(get_app_db_session),
    ) -> dict:
        identidade = await identidade_com_permissoes_locais(usuario, db)
        if permissao.value not in identidade["permissions"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Usuário sem permissão para esta operação")
        return identidade
    return verificar


@dataclass(frozen=True)
class UsuarioMock:
    username: str
    nome: str
    perfis: tuple[str, ...]


USUARIOS_MOCK: dict[str, UsuarioMock] = {
    "admin": UsuarioMock("admin", "Coordenação / Administrador", (Perfil.COORDENACAO_ADMINISTRADOR.value,)),
    "recepcionista": UsuarioMock("recepcionista", "Recepcionista SAP", (Perfil.RECEPCIONISTA.value,)),
    "macroscopia": UsuarioMock("macroscopia", "Profissional de Macroscopia", (Perfil.PROFISSIONAL_MACROSCOPIA.value,)),
    "processamento": UsuarioMock("processamento", "Técnico de Processamento", (Perfil.TECNICO_PROCESSAMENTO.value,)),
    "ihq": UsuarioMock("ihq", "Técnico de IHQ", (Perfil.TECNICO_IHQ.value,)),
    "residente": UsuarioMock("residente", "Médico Residente", (Perfil.MEDICO_RESIDENTE.value,)),
    "patologista": UsuarioMock("patologista", "Patologista / Preceptor", (Perfil.PATOLOGISTA_PRECEPTOR.value,)),
    "citotecnico": UsuarioMock("citotecnico", "Citotécnico", (Perfil.CITOTECNICO.value,)),
    "arquivo": UsuarioMock("arquivo", "Técnico do Arquivo", (Perfil.TECNICO_ARQUIVO.value,)),
    "sem-perfil": UsuarioMock("sem-perfil", "Usuário sem perfil", ()),
    "recepcao-coordenacao": UsuarioMock("recepcao-coordenacao", "Recepção + Coordenação",
                                        (Perfil.RECEPCIONISTA.value, Perfil.COORDENACAO_ADMINISTRADOR.value)),
}
