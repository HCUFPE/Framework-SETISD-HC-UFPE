from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional


class RecebimentoProviderInterface(ABC):
    """Contrato de persistência do recebimento no banco local da aplicação."""

    @abstractmethod
    async def listar_bancadas(self) -> Dict[str, Dict[str, str]]:
        """Retorna bancada e prefixo dos laboratórios ativos, por `codigo_lab`."""
        pass

    @abstractmethod
    async def listar_status_item(self) -> Dict[str, Dict[str, Any]]:
        """Retorna os status de item configurados, por código."""
        pass

    @abstractmethod
    async def listar_procedimentos_hp(self) -> List[Dict[str, Any]]:
        """Retorna os procedimentos de HP ativos."""
        pass

    @abstractmethod
    async def obter_procedimento_hp(self, procedimento_id: int) -> Optional[Dict[str, Any]]:
        """Retorna um procedimento ativo pelo id, ou None se ele não existir ou estiver inativo."""
        pass

    @abstractmethod
    async def listar_motivos(self) -> List[Dict[str, Any]]:
        """Retorna os motivos de não conformidade ativos."""
        pass

    @abstractmethod
    async def obter_motivo(self, motivo_id: int) -> Optional[Dict[str, Any]]:
        """Retorna um motivo ativo pelo id, ou None se ele não existir ou estiver inativo."""
        pass

    @abstractmethod
    async def listar_exames_da_solicitacao(self, codigo_solicitacao: str) -> List[Dict[str, Any]]:
        """Retorna os exames já registrados para a solicitação, do mais antigo ao mais recente."""
        pass

    @abstractmethod
    async def listar_historico_da_solicitacao(self, codigo_solicitacao: str) -> List[Dict[str, Any]]:
        """
        Retorna os exames da solicitação com tudo o que foi gravado sobre eles.

        Além dos campos de `listar_exames_da_solicitacao`, cada exame traz `quantidade_pecas`,
        `procedimento`, `referencia_hp`, `amostras` (com `conferencia`) e `nao_conformidades`.
        """
        pass

    @abstractmethod
    async def listar_exames_das_solicitacoes(
        self, codigos_solicitacao: List[str]
    ) -> List[Dict[str, Any]]:
        """Retorna os exames já registrados de várias solicitações, para a lista da Recepção."""
        pass

    @abstractmethod
    async def listar_codigos_com_exame_recebido(self, tipo: str) -> List[str]:
        """Retorna os códigos das solicitações que já têm exame RECEBIDO do tipo informado."""
        pass

    @abstractmethod
    async def registrar_recebimento(
        self,
        exames: List[Dict[str, Any]],
        usuario: str,
        momento: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Grava os exames recebidos e gera o nº interno de cada um em uma única transação.

        Na mesma transação, marca como resolvidas as não conformidades pendentes da
        solicitação e do tipo, e retorna os ids em `nao_conformidades_resolvidas`.
        Levanta HTTPException 409 se a solicitação já tiver sido recebida naquele tipo
        e 503 se o banco continuar ocupado após as novas tentativas.
        """
        pass

    @abstractmethod
    async def registrar_nao_conformidade(
        self,
        exames: List[Dict[str, Any]],
        dados: Dict[str, Any],
        usuario: str,
        momento: datetime,
    ) -> List[Dict[str, Any]]:
        """
        Grava os exames como devolvidos e a não conformidade, sem consumir nº interno.

        `dados` traz `motivo_id`, `observacao`, `numero_cmce` e `medico_solicitante`.
        """
        pass
