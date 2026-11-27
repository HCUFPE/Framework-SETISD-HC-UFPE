"""
Pacote de Modelos SQLAlchemy da Aplicação (`data/app.db`)
=========================================================
Centraliza a exportação de todos os modelos ORM (nativos do Framework SETISD
e específicos do Sistema de Gestão de Fila de Exames do HC-UFPE), garantindo
o registro unificado de todas as tabelas em ``Base.metadata``.
"""

from .acompanhamento_fila import (
    AcompanhamentoFila,
    REGIOES_GEOGRAFICAS_VALIDAS,
    STATUS_HIGIENIZACAO_VALIDOS,
    STATUS_OPERACIONAL_VALIDOS,
)
from .audit_log import AuditLog
from .importacao_forms import ImportacaoForms
from .incompatibilidade_exame import (
    IncompatibilidadeExame,
    TIPOS_CONFLITO_VALIDOS,
)
from .refresh_token import RefreshToken
from .regra_exame import RegraExame
from .regra_prioridade import (
    RegraPrioridade,
    TIPOS_CRITERIO_VALIDOS,
)

__all__ = [
    "AuditLog",
    "RefreshToken",
    "ImportacaoForms",
    "AcompanhamentoFila",
    "RegraPrioridade",
    "RegraExame",
    "IncompatibilidadeExame",
    "REGIOES_GEOGRAFICAS_VALIDAS",
    "STATUS_HIGIENIZACAO_VALIDOS",
    "STATUS_OPERACIONAL_VALIDOS",
    "TIPOS_CRITERIO_VALIDOS",
    "TIPOS_CONFLITO_VALIDOS",
]
