from __future__ import annotations

from Core.result import Result
from Engines.AI import AIOrchestrator, AIRequest
from Engines.Intelligence import (
    AccessMode,
    IntelligenceMetrics,
    IntelligenceRouter,
    ManualHandoffManager,
    ProviderCatalog,
    ProviderProfile,
    RoutingMode,
)

from Application.services.memory_service import MemoryService
from Application.services.project_service import ProjectService
from Application.services.workspace_service import WorkspaceApplicationService


class IntelligenceApplicationService:
    def __init__(
        self,
        catalog: ProviderCatalog,
        router: IntelligenceRouter,
        handoffs: ManualHandoffManager,
        metrics: IntelligenceMetrics,
        *,
        orchestrator: AIOrchestrator | None = None,
        memory_service: MemoryService | None = None,
        workspace_service: WorkspaceApplicationService | None = None,
        project_service: ProjectService | None = None,
    ) -> None:
        self._catalog = catalog
        self._router = router
        self._handoffs = handoffs
        self._metrics = metrics
        self._orchestrator = orchestrator
        self._memory_service = memory_service
        self._workspace_service = workspace_service
        self._project_service = project_service

    def register_provider_profile(self, profile: ProviderProfile) -> Result:
        return self._catalog.register(profile)

    def list_provider_profiles(self) -> Result:
        return Result.success(
            message="ProviderProfiles listados",
            data=self._catalog.list(),
        )

    def route(
        self,
        *,
        prompt: str | None,
        capability: str | None = "general_assistance",
        mode: RoutingMode = RoutingMode.FREE_ONLY,
    ) -> Result:
        request = self._request(prompt, capability)
        if not request.is_success:
            self._metrics.record_failure()
            return request
        result = self._router.route(request.data, mode=mode)
        if result.is_success:
            self._metrics.record_selection(
                result.data.selected_provider_id,
                result.data.routing_mode,
            )
        else:
            self._metrics.record_failure()
        return result

    def create_manual_handoff(
        self,
        *,
        provider_id: str | None,
        prompt: str | None,
        workspace_id: str | None = None,
        project_id: str | None = None,
        mission_id: str | None = None,
    ) -> Result:
        profile = self._catalog.get(provider_id)
        if not profile.is_success:
            return profile
        if not profile.data.enabled:
            return Result.error(message="ProviderProfile está desabilitado")
        if profile.data.access_mode is not AccessMode.MANUAL:
            return Result.error(message="Provider não utiliza handoff manual")
        related = self._validate_relations(workspace_id, project_id)
        if not related.is_success:
            return related
        return self._handoffs.create(
            provider_id=provider_id,
            prompt=prompt,
            workspace_id=workspace_id,
            project_id=project_id,
            mission_id=mission_id,
        )

    def complete_manual_handoff(
        self,
        handoff_id: str | None,
        *,
        response: str | None,
        save_as_memory: bool = False,
        memory_category: str = "intelligence",
    ) -> Result:
        completed = self._handoffs.complete(handoff_id, response=response)
        if not completed.is_success:
            self._metrics.record_failure()
            return completed
        handoff = completed.data
        if save_as_memory:
            stored = self._store_handoff_memory(
                handoff,
                category=memory_category,
            )
            if not stored.is_success:
                self._metrics.record_failure()
                return Result.error(
                    message=(
                        "Handoff concluído, mas a Memory não foi armazenada: "
                        f"{stored.message}"
                    ),
                    data=handoff,
                )
        self._metrics.record_success()
        return completed

    def list_manual_handoffs(self) -> Result:
        return Result.success(
            message="ManualHandoffs listados",
            data=self._handoffs.list(),
        )

    def execute_automatic(
        self,
        *,
        prompt: str | None,
        capability: str | None = "text_generation",
        mode: RoutingMode = RoutingMode.LOCAL_FIRST,
    ) -> Result:
        routed = self.route(
            prompt=prompt,
            capability=capability,
            mode=mode,
        )
        if not routed.is_success:
            return routed
        decision = routed.data
        if decision.requires_manual_handoff:
            return Result.error(
                message="Provider selecionado requer ManualHandoff",
                data=decision,
            )
        if self._orchestrator is None:
            self._metrics.record_failure()
            return Result.error(message="AIOrchestrator não está disponível")
        result = self._orchestrator.generate_with_order(
            AIRequest(prompt=prompt.strip(), capability=capability.strip()),
            (
                decision.selected_provider_id,
                *decision.alternatives,
            ),
        )
        if result.is_success:
            self._metrics.record_success()
        else:
            self._metrics.record_failure()
        return result

    def metrics(self) -> Result:
        return Result.success(
            message="Métricas de Intelligence listadas",
            data=self._metrics.snapshot(),
        )

    @staticmethod
    def _request(prompt: str | None, capability: str | None) -> Result:
        if not isinstance(prompt, str) or not prompt.strip():
            return Result.error(message="Prompt deve ser texto não vazio")
        if not isinstance(capability, str) or not capability.strip():
            return Result.error(message="Capability deve ser texto não vazio")
        return Result.success(
            message="AIRequest criado",
            data=AIRequest(
                prompt=prompt.strip(),
                capability=capability.strip(),
            ),
        )

    def _validate_relations(
        self,
        workspace_id: str | None,
        project_id: str | None,
    ) -> Result:
        if workspace_id and self._workspace_service is not None:
            workspace = self._workspace_service.get(workspace_id)
            if not workspace.is_success:
                return workspace
        if project_id and self._project_service is not None:
            project = self._project_service.get(project_id)
            if not project.is_success:
                return project
            if workspace_id and project.data.workspace_id != workspace_id:
                return Result.error(
                    message="Projeto não pertence ao Workspace informado"
                )
        return Result.success(message="Relações validadas")

    def _store_handoff_memory(self, handoff, *, category: str) -> Result:
        if self._memory_service is None:
            return Result.error(message="MemoryService não está disponível")
        if not handoff.workspace_id:
            return Result.error(message="Workspace é obrigatório para Memory")
        return self._memory_service.store(
            workspace_id=handoff.workspace_id,
            mission_id=handoff.mission_id,
            category=category,
            title=f"Resposta manual — {handoff.provider_id}",
            content=handoff.response,
            metadata={
                "handoff_id": handoff.id,
                "provider_id": handoff.provider_id,
                "project_id": handoff.project_id,
            },
        )
