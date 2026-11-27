"""Contrato de persistência para operações já existentes da Recepção."""

from abc import ABC, abstractmethod
from typing import Any


class ReceptionProviderInterface(ABC):
    """Define consultas e gravações independentes da origem dos dados."""

    @abstractmethod
    async def seed_solicitacoes(self, solicitacoes: list[dict[str, Any]]) -> None:
        """Insere solicitações de fixture ausentes sem sobrescrever estado existente."""

    @abstractmethod
    async def buscar_solicitacao(self, codigo: str) -> dict[str, Any] | None:
        """Retorna grupo de exame pela chave composta normalizada."""

    @abstractmethod
    async def listar_exames_da_solicitacao(self, codigo: str) -> list[dict[str, Any]]:
        """Retorna todos os grupos de exame de um código AGHU."""

    @abstractmethod
    async def listar_solicitacoes_pendentes(self) -> list[dict[str, Any]]:
        """Lista solicitações aguardando recebimento por data crescente."""

    @abstractmethod
    async def contar_solicitacoes_pendentes(self) -> int:
        """Conta solicitações aguardando recebimento."""

    @abstractmethod
    async def salvar_solicitacao(self, payload: dict[str, Any]) -> None:
        """Insere ou atualiza os campos locais da solicitação."""

    @abstractmethod
    async def cancelar_solicitacao(self, grupo_id: str, cancelamento: dict[str, Any]) -> dict[str, Any] | None:
        """Atualiza o grupo pendente de forma condicional para evitar corrida com recebimento."""

    @abstractmethod
    async def listar_casos(self) -> list[dict[str, Any]]:
        """Lista casos com relações necessárias às telas existentes."""

    @abstractmethod
    async def buscar_caso(self, numero: str) -> dict[str, Any] | None:
        """Consulta caso por número interno."""

    @abstractmethod
    async def salvar_caso(self, payload: dict[str, Any]) -> None:
        """Insere ou atualiza o agregado de caso."""

    @abstractmethod
    async def adicionar_conferencia(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Persiste conferência e retorna o registro com identificador."""

    @abstractmethod
    async def adicionar_materiais(self, caso_numero: str, materiais: list[dict[str, Any]]) -> None:
        """Persiste os materiais gerados na Recepção."""

    @abstractmethod
    async def adicionar_ihq(self, caso_numero: str, solicitacao_id: str, exame: dict[str, Any]) -> None:
        """Persiste o vínculo de IHQ recebido para o caso de origem."""

    @abstractmethod
    async def adicionar_historico(self, caso_numero: str, evento: dict[str, Any]) -> dict[str, Any]:
        """Acrescenta evento imutável ao histórico e retorna seu identificador."""

    @abstractmethod
    async def adicionar_nao_conformidade(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Persiste não conformidade e retorna o registro com identificador."""

    @abstractmethod
    async def adicionar_devolucao(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Persiste devolução e retorna o registro com identificador."""

    @abstractmethod
    async def listar_devolucoes(self) -> list[dict[str, Any]]:
        """Lista devoluções com suas não conformidades."""

    @abstractmethod
    async def atualizar_situacao_devolucao(self, devolucao_id: int, situacao: str) -> dict[str, Any] | None:
        """Atualiza situação e retorna os estados anterior/atual sem confirmar a transação."""

    @abstractmethod
    async def associar_ocorrencias_reabertas(self, solicitacao_id: str, caso_numero: str) -> list[dict[str, Any]]:
        """Associa ao caso as ocorrências de rejeição pré-recepção regularizadas para o grupo."""
