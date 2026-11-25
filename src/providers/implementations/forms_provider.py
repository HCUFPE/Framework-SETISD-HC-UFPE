"""
Provedores de respostas do Microsoft Forms (abordagem híbrida)
==============================================================
`PowerAutomateFormsProvider` usa o payload enviado pelo fluxo do Power
Automate. `MockFormsProvider` é o padrão de desenvolvimento e aceita o mesmo
payload quando presente. `FormsApiProvider` é o ponto de extensão reservado
para o pull via REST não oficial do Forms.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ...config import settings
from ...helpers.string_helper import obter_campo, parse_datetime
from ..interfaces.forms_provider_interface import FormsProviderInterface

EXAME_MOCK = {
    "codigoExame": "CMDIP",
    "nomeExame": "CINTILOGRAFIA DO MIOCARDIO COM DIPIRIDAMOL",
}


class _BaseFormsProvider(FormsProviderInterface):
    """Normalização compartilhada pelos provedores de formulário."""

    def _normalizar(
        self,
        response_id: str,
        payload: Optional[Dict[str, Any]],
        usar_mock_quando_vazio: bool,
    ) -> Dict[str, Any]:
        resposta: Dict[str, Any] = {}
        for chave, apelidos in settings.FORMS_FIELD_MAP.items():
            resposta[chave] = obter_campo(payload or {}, apelidos)

        if usar_mock_quando_vazio:
            if not resposta.get("nome"):
                resposta["nome"] = f"PACIENTE FORMS {response_id[:8].upper()}"
            if not resposta.get("prontuario"):
                resposta["prontuario"] = hashlib.sha256(response_id.encode("utf-8")).hexdigest()[:8]
            if not resposta.get("telefone"):
                resposta["telefone"] = "81999999999"
            if not resposta.get("codigoExame") and not resposta.get("nomeExame"):
                resposta["codigoExame"] = EXAME_MOCK["codigoExame"]
                resposta["nomeExame"] = EXAME_MOCK["nomeExame"]
        elif not payload:
            raise ValueError("O payload do Power Automate não foi enviado no webhook.")

        resposta["responseId"] = response_id
        resposta["submittedAt"] = parse_datetime(
            resposta.get("submittedAt"), datetime.now(timezone.utc)
        )
        return resposta

    async def buscar_resposta(
        self,
        form_id: str,
        response_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError


class MockFormsProvider(_BaseFormsProvider):
    """Provedor determinístico para desenvolvimento e testes."""

    async def buscar_resposta(
        self,
        form_id: str,
        response_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Usa o payload do webhook quando presente; completa campos ausentes."""
        return self._normalizar(response_id, payload, usar_mock_quando_vazio=True)


class PowerAutomateFormsProvider(_BaseFormsProvider):
    """Usa exclusivamente os dados obtidos pela ação 'Obter detalhes da resposta'."""

    async def buscar_resposta(
        self,
        form_id: str,
        response_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Normaliza o payload real sem inventar nenhum valor."""
        if not payload:
            raise ValueError("O payload do Power Automate não foi enviado no webhook.")
        return self._normalizar(response_id, payload, usar_mock_quando_vazio=False)


class FormsApiProvider(_BaseFormsProvider):
    """Reservado para o pull via API não oficial `forms.office.com/formapi`."""

    async def buscar_resposta(
        self,
        form_id: str,
        response_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Avisa que a integração por pull ainda não foi habilitada."""
        raise NotImplementedError(
            "FORMS_API ainda não implementada: use POWER_AUTOMATE ou MOCK. "
            f"Base configurada: {settings.FORMS_API_BASE_URL}"
        )
