from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Sequence


class SolicitacaoProviderInterface(ABC):
    """Contrato de LEITURA das solicitações do AGHU (RN-01: nunca escreve no AGHU)."""

    @abstractmethod
    async def obter_solicitacao_por_codigo(self, codigo: str) -> Optional[Dict[str, Any]]:
        """
        Retorna a solicitação com todas as suas amostras, ou None se ela não existir.

        Formato de retorno (montado por `montar_solicitacao`):
            {
                "codigo": str, "data_solicitacao": str | None (AAAA-MM-DD),
                "nome_paciente": str (só iniciais), "data_nascimento": str | None (AAAA-MM-DD),
                "prontuario": str | None, "especialidade": str | None, "convenio": str | None,
                "origem": str, "unidade": str | None, "informacoes_clinica": str | None,
                "itens": [{
                    "numero_amostra": int, "codigo_lab": str, "sigla_exame": str,
                    "nome_exame": str, "descricao_material": str | None,
                    "cod_status_item": str, "status_item_exame": str
                }]
            }

        A conversão de `codigo_lab` em bancada e a regra de status ficam no controller.
        """
        pass

    @abstractmethod
    async def listar_solicitacoes(
        self,
        pagina: int,
        por_pagina: int,
        codigos_status: Optional[Sequence[str]],
        codigos_lab: Sequence[str],
    ) -> Dict[str, Any]:
        """
        Retorna uma página de solicitações, da mais recente para a mais antiga.

        Entram as que têm ao menos uma amostra de `codigos_lab` e, se `codigos_status` não
        for None, com um desses status. Cada solicitação vem completa, no mesmo formato de
        `obter_solicitacao_por_codigo`.

        Formato de retorno: {"total": int, "solicitacoes": [...]}
        """
        pass
