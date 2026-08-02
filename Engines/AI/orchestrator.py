from collections.abc import Iterable

from Core.registry import Registry
from Core.result import Result
from Engines.AI.models import (
    AIOrchestrationFailure,
    AIProviderAttempt,
    AIRequest,
    AIResponse,
)
from Engines.AI.provider import AIProvider


class AIOrchestrator:
    def __init__(
        self,
        registry: Registry,
        provider_id: str | None = None,
        *,
        provider_ids: Iterable[str] | None = None,
    ) -> None:
        if provider_id is not None and provider_ids is not None:
            raise ValueError(
                "Use provider_id ou provider_ids, não ambos"
            )

        self._registry = registry
        self._provider_ids = (
            tuple(provider_ids)
            if provider_ids is not None
            else (provider_id,) if provider_id is not None else ()
        )

    @property
    def provider_ids(self) -> tuple[str, ...]:
        return self._provider_ids

    def generate(self, request: AIRequest) -> Result:
        attempts: list[AIProviderAttempt] = []
        compatible_provider_found = False

        for provider_id in self._provider_ids:
            try:
                provider = self._registry.get(provider_id)
            except ValueError:
                attempts.append(
                    AIProviderAttempt(provider_id, "missing")
                )
                continue

            if not isinstance(provider, AIProvider):
                attempts.append(
                    AIProviderAttempt(provider_id, "invalid_provider")
                )
                continue

            if provider.provider_id != provider_id:
                attempts.append(
                    AIProviderAttempt(provider_id, "identity_mismatch")
                )
                continue

            if request.capability not in provider.capabilities:
                continue

            compatible_provider_found = True

            try:
                result = provider.generate(request)
            except Exception as error:
                attempts.append(
                    AIProviderAttempt(
                        provider_id=provider_id,
                        outcome="exception",
                        error_type=type(error).__name__,
                    )
                )
                continue

            if not isinstance(result, Result):
                attempts.append(
                    AIProviderAttempt(provider_id, "invalid_result")
                )
                continue

            if not result.is_success:
                attempts.append(
                    AIProviderAttempt(provider_id, "error")
                )
                continue

            if not isinstance(result.data, AIResponse):
                attempts.append(
                    AIProviderAttempt(provider_id, "invalid_response")
                )
                continue

            if result.data.provider_id != provider.provider_id:
                attempts.append(
                    AIProviderAttempt(
                        provider_id,
                        "invalid_response_provider",
                    )
                )
                continue

            return result

        failure = AIOrchestrationFailure(
            capability=request.capability,
            attempts=tuple(attempts),
        )

        if not compatible_provider_found:
            return Result.error(
                message=(
                    "Nenhum provedor compatível disponível para: "
                    f"{request.capability}"
                ),
                data=failure,
            )

        return Result.error(
            message=(
                "Todos os provedores compatíveis falharam para: "
                f"{request.capability}"
            ),
            data=failure,
        )
