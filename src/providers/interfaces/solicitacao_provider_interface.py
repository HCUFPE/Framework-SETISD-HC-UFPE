from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Sequence

# Colunas da lista da Recepção que vêm do AGHU e, por isso, podem ser filtradas e ordenadas
# antes da paginação. Situação e números internos vêm do banco local e ficam de fora.
COLUNAS_ORDENAVEIS = ("codigo", "data", "paciente", "prontuario", "origem", "clinica")
COLUNAS_FILTRAVEIS = COLUNAS_ORDENAVEIS

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
        codigos_lab_urgentes: Sequence[str] = (),
        codigos_excluidas_da_prioridade: Sequence[str] = (),
        consulta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Retorna uma página de solicitações: as prioritárias primeiro e, dentro de cada grupo,
        da mais recente para a mais antiga.

        Entram as que têm ao menos uma amostra de `codigos_lab` e, se `codigos_status` não
        for None, com um desses status. Cada solicitação vem completa, no mesmo formato de
        `obter_solicitacao_por_codigo`.

        É prioritária a solicitação com ao menos uma amostra de `codigos_lab_urgentes` cujo
        código não esteja em `codigos_excluidas_da_prioridade` (as já recebidas). A prioridade
        vale para a ordenação antes da paginação, então vale entre as páginas.

        `consulta` traz os filtros e a ordenação pedidos pelo usuário, todos aplicados antes da
        paginação e do total (chaves opcionais):
        - "filtros": {coluna: texto}, com as colunas de COLUNAS_FILTRAVEIS. Os textos casam por
          "contém", sem diferenciar maiúsculas; "data" é um dia AAAA-MM-DD exato.
        - "codigos_lab_filtro": só entram solicitações com amostra desses laboratórios (None não
          filtra; lista vazia não casa com nada).
        - "ordenar_por": uma das COLUNAS_ORDENAVEIS, e "direcao": "asc" ou "desc". Empates
          seguem da mais recente para a mais antiga.

        Formato de retorno: {"total": int, "solicitacoes": [...]}
        """
        pass
    