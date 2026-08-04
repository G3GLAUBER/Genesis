from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from Application.models import (
    MissionCopilotContext,
    MissionCopilotRequest,
    MissionCopilotResult,
)
from Application.services.intelligence_service import (
    IntelligenceApplicationService,
)
from Application.services.memory_service import MemoryService
from Application.services.mission_service import MissionApplicationService
from Application.services.project_service import ProjectService
from Application.services.workspace_service import WorkspaceApplicationService
from Core.result import Result
from Engines.Intelligence import HandoffStatus, RoutingMode


class MissionCopilotApplicationService:
    """Coordinates the human-reviewed Mission Copilot application flow."""

    def __init__(
        self,
        mission_service: MissionApplicationService,
        intelligence_service: IntelligenceApplicationService,
        memory_service: MemoryService,
        project_service: ProjectService,
        workspace_service: WorkspaceApplicationService,
    ) -> None:
        self._mission_service = mission_service
        self._intelligence_service = intelligence_service
        self._memory_service = memory_service
        self._project_service = project_service
        self._workspace_service = workspace_service
        self._requests: dict[str, MissionCopilotRequest] = {}
        self._handoff_ids: dict[str, str] = {}
        self._raw_responses: dict[str, str] = {}
        self._results: dict[str, MissionCopilotResult] = {}
        self._result_ids_by_mission: dict[str, str] = {}
        self._lock = RLock()

    def create_mission_copilot_request(
        self,
        *,
        title: str | None,
        objective: str | None,
        workspace_id: str | None = None,
        project_id: str | None = None,
        constraints: Iterable[str] | str | None = (),
        expected_result: str | None = None,
    ) -> Result:
        selected_workspace_id = (
            workspace_id or self._workspace_service.active_workspace_id
        )
        workspace_result = self._workspace_service.get(selected_workspace_id)
        if not workspace_result.is_success:
            return workspace_result
        workspace = workspace_result.data

        project = None
        if project_id:
            project_result = self._project_service.get(project_id)
            if not project_result.is_success:
                return project_result
            project = project_result.data
            if project.workspace_id != workspace.id:
                return Result.error(
                    message="Project não pertence ao Workspace informado"
                )

        normalized_expected = self._optional_text(expected_result)
        mission_result = self._mission_service.create_mission(
            title=title,
            objective=objective,
            source="Mission Copilot",
            constraints=constraints,
            success_criteria=(normalized_expected,) if normalized_expected else (),
        )
        if not mission_result.is_success:
            return mission_result
        mission = mission_result.data

        workspace_association = self._workspace_service.associate_mission(
            workspace.id,
            mission_id=mission.id,
        )
        if not workspace_association.is_success:
            return workspace_association
        if project is not None:
            project_association = self._project_service.attach_mission(
                project.id,
                mission_id=mission.id,
            )
            if not project_association.is_success:
                return project_association
            project = project_association.data

        memories_result = self._memory_service.history(workspace_id=workspace.id)
        memories = memories_result.data[:5] if memories_result.is_success else ()
        context = MissionCopilotContext(
            workspace_id=workspace.id,
            workspace_name=workspace.name,
            project_id=project.id if project is not None else None,
            project_title=project.title if project is not None else None,
            project_client=project.client if project is not None else None,
            project_address=project.address if project is not None else None,
            project_description=(
                project.description if project is not None else None
            ),
            constraints=mission.constraints,
            memories=memories,
            expected_result=normalized_expected,
        )
        prompt = self._build_prompt(mission, context)
        routed = self._intelligence_service.route(
            prompt=prompt,
            capability="general_assistance",
            mode=RoutingMode.FREE_ONLY,
        )
        if not routed.is_success:
            return routed
        request = MissionCopilotRequest(
            mission=mission,
            context=context,
            prompt=prompt,
            decision=routed.data,
            created_at=datetime.now(timezone.utc),
        )
        with self._lock:
            self._requests[mission.id] = request
        return Result.success(
            message="Missão criada e contexto preparado para o Copilot",
            data=request,
        )

    def create_handoff(self, mission_id: str | None) -> Result:
        request_result = self.get_request(mission_id)
        if not request_result.is_success:
            return request_result
        request = request_result.data
        if not request.decision.requires_manual_handoff:
            return Result.error(
                message="Provider recomendado não utiliza ManualHandoff"
            )
        with self._lock:
            existing_id = self._handoff_ids.get(request.mission.id)
        if existing_id:
            return self.get_handoff(request.mission.id)
        created = self._intelligence_service.create_manual_handoff(
            provider_id=request.decision.selected_provider_id,
            prompt=request.prompt,
            workspace_id=request.context.workspace_id,
            project_id=request.context.project_id,
            mission_id=request.mission.id,
        )
        if created.is_success:
            with self._lock:
                self._handoff_ids[request.mission.id] = created.data.id
        return created

    def complete_handoff(
        self,
        mission_id: str | None,
        handoff_id: str | None,
        *,
        response: str | None,
    ) -> Result:
        related = self._related_handoff(mission_id, handoff_id)
        if not related.is_success:
            return related
        if not isinstance(response, str) or not response.strip():
            return Result.error(message="Resposta JSON deve ser texto não vazio")
        validated = self._parse_response(response)
        if not validated.is_success:
            return validated
        completed = self._intelligence_service.complete_manual_handoff(
            handoff_id,
            response=response,
            save_as_memory=False,
        )
        if completed.is_success:
            with self._lock:
                self._raw_responses[completed.data.id] = response
        return completed

    def build_result(
        self,
        mission_id: str | None,
        handoff_id: str | None,
    ) -> Result:
        related = self._related_handoff(mission_id, handoff_id)
        if not related.is_success:
            return related
        handoff = related.data
        if handoff.status is not HandoffStatus.COMPLETED:
            return Result.error(message="ManualHandoff ainda não foi concluído")
        with self._lock:
            raw_response = self._raw_responses.get(handoff.id, handoff.response)
        parsed = self._parse_response(raw_response)
        if not parsed.is_success:
            return parsed
        request = self.get_request(mission_id).data
        values = parsed.data
        result = MissionCopilotResult(
            id=str(uuid4()),
            mission_id=request.mission.id,
            workspace_id=request.context.workspace_id,
            project_id=request.context.project_id,
            provider_id=handoff.provider_id,
            routing_mode=request.decision.routing_mode,
            prompt=request.prompt,
            raw_response=raw_response,
            summary=values.get("summary"),
            suggested_actions=values.get("suggested_actions"),
            risks=values.get("risks"),
            assumptions=values.get("assumptions"),
            created_at=datetime.now(timezone.utc),
        )
        with self._lock:
            self._results[result.id] = result
            self._result_ids_by_mission[result.mission_id] = result.id
        return Result.success(
            message="Resultado do Mission Copilot criado",
            data=result,
        )

    def save_result_as_memory(self, result_id: str | None) -> Result:
        result = self.get_result(result_id)
        if not result.is_success:
            return result
        item = result.data
        content = item.summary or item.raw_response
        stored = self._memory_service.store(
            workspace_id=item.workspace_id,
            mission_id=item.mission_id,
            category="mission_copilot",
            title="Resultado do Mission Copilot",
            content=content,
            metadata={
                "mission_copilot_result_id": item.id,
                "provider_id": item.provider_id,
                "project_id": item.project_id,
                "raw_response": item.raw_response,
            },
        )
        if not stored.is_success:
            return stored
        return Result.success(
            message="Resultado salvo na Memory",
            data=stored.data,
        )

    def get_request(self, mission_id: str | None) -> Result:
        normalized = self._optional_text(mission_id)
        with self._lock:
            request = self._requests.get(normalized or "")
        if request is None:
            return Result.error(message="Pedido do Mission Copilot não encontrado")
        return Result.success(
            message="Pedido do Mission Copilot encontrado",
            data=request,
        )

    def get_handoff(self, mission_id: str | None) -> Result:
        normalized = self._optional_text(mission_id)
        with self._lock:
            handoff_id = self._handoff_ids.get(normalized or "")
        if not handoff_id:
            return Result.error(message="ManualHandoff da missão não encontrado")
        handoffs = self._intelligence_service.list_manual_handoffs()
        if not handoffs.is_success:
            return handoffs
        handoff = next(
            (item for item in handoffs.data if item.id == handoff_id),
            None,
        )
        if handoff is None:
            return Result.error(message="ManualHandoff da missão não encontrado")
        return Result.success(message="ManualHandoff encontrado", data=handoff)

    def get_result(self, result_id: str | None) -> Result:
        normalized = self._optional_text(result_id)
        with self._lock:
            result = self._results.get(normalized or "")
        if result is None:
            return Result.error(message="Resultado do Mission Copilot não encontrado")
        return Result.success(
            message="Resultado do Mission Copilot encontrado",
            data=result,
        )

    def get_result_for_mission(self, mission_id: str | None) -> Result:
        normalized = self._optional_text(mission_id)
        with self._lock:
            result_id = self._result_ids_by_mission.get(normalized or "")
        if not result_id:
            return Result.error(message="A missão ainda não possui resultado")
        return self.get_result(result_id)

    def _related_handoff(
        self,
        mission_id: str | None,
        handoff_id: str | None,
    ) -> Result:
        handoff = self.get_handoff(mission_id)
        if not handoff.is_success:
            return handoff
        if handoff.data.id != self._optional_text(handoff_id):
            return Result.error(message="ManualHandoff não pertence à missão")
        return handoff

    @classmethod
    def _parse_response(cls, raw_response: str | None) -> Result:
        if not isinstance(raw_response, str) or not raw_response.strip():
            return Result.error(message="Resposta JSON deve ser texto não vazio")
        try:
            values = json.loads(raw_response)
        except json.JSONDecodeError as error:
            return Result.error(
                message=(
                    "Resposta JSON inválida: "
                    f"linha {error.lineno}, coluna {error.colno}"
                )
            )
        if not isinstance(values, dict):
            return Result.error(message="Resposta JSON deve ser um objeto")
        summary = values.get("summary")
        if summary is not None and (
            not isinstance(summary, str) or not summary.strip()
        ):
            return Result.error(message="summary deve ser texto não vazio")
        parsed = {"summary": summary.strip() if summary is not None else None}
        for field in ("suggested_actions", "risks", "assumptions"):
            items = values.get(field)
            if items is None:
                parsed[field] = None
                continue
            if not isinstance(items, list) or any(
                not isinstance(item, str) or not item.strip() for item in items
            ):
                return Result.error(
                    message=f"{field} deve ser uma lista de textos não vazios"
                )
            parsed[field] = tuple(item.strip() for item in items)
        return Result.success(message="Resposta JSON validada", data=parsed)

    @staticmethod
    def _build_prompt(mission, context: MissionCopilotContext) -> str:
        sections = [
            "Você está apoiando uma missão no Genesis.",
            f"Workspace: {context.workspace_name}",
        ]
        if context.project_id:
            sections.extend(
                (
                    f"Project: {context.project_title}",
                    f"Cliente: {context.project_client}",
                    f"Local: {context.project_address}",
                )
            )
            if context.project_description:
                sections.append(
                    f"Descrição do Project: {context.project_description}"
                )
        sections.extend(
            (
                f"Missão: {mission.title}",
                f"Objetivo: {mission.objective}",
            )
        )
        if context.constraints:
            sections.append("Constraints:\n- " + "\n- ".join(context.constraints))
        if context.memories:
            memory_lines = (
                f"- {item.title}: {item.content}" for item in context.memories
            )
            sections.append("Memories relevantes:\n" + "\n".join(memory_lines))
        if context.expected_result:
            sections.append(f"Resultado esperado: {context.expected_result}")
        sections.append(
            "Responda somente com um objeto JSON válido usando os campos "
            "opcionais summary (texto), suggested_actions (lista de textos), "
            "risks (lista de textos) e assumptions (lista de textos). "
            "Não execute ações e não invente contexto ausente."
        )
        return "\n\n".join(sections)

    @staticmethod
    def _optional_text(value: object) -> str | None:
        return value.strip() if isinstance(value, str) and value.strip() else None
