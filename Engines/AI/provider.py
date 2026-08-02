from abc import ABC, abstractmethod

from Core.result import Result
from Engines.AI.models import AIRequest


class AIProvider(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Retorna o identificador único do provedor."""

    @property
    @abstractmethod
    def capabilities(self) -> tuple[str, ...]:
        """Retorna as capacidades suportadas pelo provedor."""

    @abstractmethod
    def generate(self, request: AIRequest) -> Result:
        """Gera uma resposta padronizada para a solicitação."""
