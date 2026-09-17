"""
Helper Utilitário de Registro de Auditoria e Trilha de Mudanças
================================================================
Função padronizada para registrar logs de auditoria em rotas e controllers.
"""

import json
import logging
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.audit_log import AuditLog

logger = logging.getLogger("audit")


async def registrar_auditoria(
    db: AsyncSession,
    usuario: str,
    categoria: str,
    acao: str,
    recurso: str,
    dados_anteriores: Optional[Any] = None,
    dados_novos: Optional[Any] = None,
    ip_origem: Optional[str] = None
) -> AuditLog:
    """
    Registra um evento de auditoria no banco de dados local da aplicação.

    Exemplos usando os perfis reais do sistema (ADMINISTRADOR, MEDICO, ENFERMAGEM):
        # 1. Categoria SEGURANCA (Ex: ADMINISTRADOR alterando perfil):
        await registrar_auditoria(
            db=session,
            usuario="gestor.admin",
            categoria="SEGURANCA",
            acao="ALTERAR_PERFIL_USUARIO",
            recurso="usuario:joao.silva",
            dados_anteriores={"perfil": "ENFERMAGEM"},
            dados_novos={"perfil": "MEDICO"},
            ip_origem=request.client.host
        )

        # 2. Categoria NEGOCIO_CLINICO (Ex: MEDICO concedendo alta):
        await registrar_auditoria(
            db=session,
            usuario="dr.carlos",
            categoria="NEGOCIO_CLINICO",
            acao="REGISTRAR_ALTA_PACIENTE",
            recurso="paciente:12345",
            dados_anteriores={"status_internacao": "EM_UTI"},
            dados_novos={"status_internacao": "ALTA_MEDICA"},
            ip_origem=request.client.host
        )
    """
    try:
        str_anteriores = json.dumps(dados_anteriores, ensure_ascii=False, default=str) if dados_anteriores is not None else None
        str_novos = json.dumps(dados_novos, ensure_ascii=False, default=str) if dados_novos is not None else None

        log_entry = AuditLog(
            usuario=usuario,
            categoria=categoria.upper(),
            acao=acao.upper(),
            recurso=recurso,
            dados_anteriores=str_anteriores,
            dados_novos=str_novos,
            ip_origem=ip_origem
        )

        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)

        logger.info(f"AuditLog #{log_entry.id} registrado: [{categoria}] {usuario} -> {acao} em {recurso}")
        return log_entry

    except Exception as e:
        logger.error(f"Erro ao gravar log de auditoria: {e}")
        await db.rollback()
        raise e
