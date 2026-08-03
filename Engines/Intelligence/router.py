from __future__ import annotations

from Core.result import Result
from Engines.AI import AIRequest
from Engines.Intelligence.catalog import ProviderCatalog
from Engines.Intelligence.models import RoutingDecision, RoutingMode
from Engines.Intelligence.policies import eligible_profiles, routing_reason


class IntelligenceRouter:
    def __init__(self, catalog: ProviderCatalog) -> None:
        self._catalog = catalog

    def route(
        self,
        request: AIRequest,
        *,
        mode: RoutingMode = RoutingMode.FREE_ONLY,
    ) -> Result:
        if not isinstance(request, AIRequest):
            return Result.error(message="AIRequest inválido")
        if not isinstance(mode, RoutingMode):
            return Result.error(message="RoutingMode inválido")
        if not isinstance(request.capability, str):
            return Result.error(message="Capability deve ser texto não vazio")
        capability = request.capability.strip()
        if not capability:
            return Result.error(message="Capability deve ser texto não vazio")
        ordered = eligible_profiles(
            self._catalog.list(),
            capability=capability,
            mode=mode,
        )
        if not ordered:
            return Result.error(
                message=f"Nenhum provider compatível para {capability}"
            )
        selected = ordered[0]
        decision = RoutingDecision(
            request_capability=capability,
            prompt=request.prompt,
            selected_provider_id=selected.provider_id,
            routing_mode=mode,
            access_mode=selected.access_mode,
            reason=routing_reason(selected, mode),
            alternatives=tuple(item.provider_id for item in ordered[1:]),
            requires_manual_handoff=(selected.access_mode.value == "manual"),
        )
        return Result.success(message="Roteamento concluído", data=decision)
