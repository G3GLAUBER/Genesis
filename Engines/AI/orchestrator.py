from Core.registry import Registry
from Core.result import Result
from Engines.AI.models import AIRequest
from Engines.AI.provider import AIProvider


class AIOrchestrator:
    def __init__(self, registry: Registry, provider_id: str) -> None:
        self._registry = registry
        self._provider_id = provider_id

    def generate(self, request: AIRequest) -> Result:
        try:
            provider = self._registry.get(self._provider_id)
        except ValueError:
            return Result.error(
                message=(
                    "Provedor de IA não encontrado: "
                    f"{self._provider_id}"
                ),
            )

        if not isinstance(provider, AIProvider):
            return Result.error(
                message=(
                    "Item registrado não implementa AIProvider: "
                    f"{self._provider_id}"
                ),
            )

        if provider.provider_id != self._provider_id:
            return Result.error(
                message=(
                    "Identificador do provedor não corresponde ao registro: "
                    f"esperado '{self._provider_id}', "
                    f"recebido '{provider.provider_id}'"
                ),
            )

        if request.capability not in provider.capabilities:
            return Result.error(
                message=(
                    f"Capacidade não suportada pelo provedor "
                    f"'{provider.provider_id}': {request.capability}"
                ),
            )

        return provider.generate(request)
