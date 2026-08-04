from __future__ import annotations

from dataclasses import replace
from threading import RLock
from uuid import uuid4

from Core.result import Result
from Engines.Remodeling.models import (
    ProposalStatus,
    RemodelingBrief,
    RemodelingProposal,
)
from Engines.Remodeling.proposal import parse_proposal
from Engines.Remodeling.validation import (
    deadline_value,
    decimal_value,
    missing_information,
    optional_text,
    required_text,
    text_tuple,
)


class RemodelingEngine:
    def __init__(self) -> None:
        self._briefs: dict[str, RemodelingBrief] = {}
        self._proposals: dict[str, RemodelingProposal] = {}
        self._lock = RLock()

    def create_brief(self, **values) -> Result:
        try:
            brief = RemodelingBrief(
                id=str(uuid4()),
                project_id=required_text(values.get("project_id"), "project_id"),
                workspace_id=required_text(
                    values.get("workspace_id"), "workspace_id"
                ),
                project_type=required_text(
                    values.get("project_type"), "project_type"
                ),
                room_length=decimal_value(
                    values.get("room_length"), "room_length", positive=True
                ),
                room_width=decimal_value(
                    values.get("room_width"), "room_width", positive=True
                ),
                room_height=decimal_value(
                    values.get("room_height"), "room_height", positive=True
                ),
                current_condition=required_text(
                    values.get("current_condition"), "current_condition"
                ),
                desired_result=required_text(
                    values.get("desired_result"), "desired_result"
                ),
                budget_limit=decimal_value(
                    values.get("budget_limit"), "budget_limit"
                ),
                deadline=deadline_value(values.get("deadline")),
                constraints=text_tuple(values.get("constraints"), "constraints"),
                client_preferences=text_tuple(
                    values.get("client_preferences"), "client_preferences"
                ),
                known_materials=text_tuple(
                    values.get("known_materials"), "known_materials"
                ),
                notes=optional_text(values.get("notes"), "notes"),
            )
        except ValueError as error:
            return Result.error(message=f"Brief inválido: {error}")
        with self._lock:
            self._briefs[brief.id] = brief
        return Result.success(message="Brief criado", data=brief)

    def validate_brief(self, brief: object) -> Result:
        if not isinstance(brief, RemodelingBrief):
            return Result.error(message="Brief inválido")
        return Result.success(message="Brief válido", data=brief)

    def get_brief(self, brief_id: str | None) -> Result:
        with self._lock:
            brief = self._briefs.get(brief_id or "")
        if brief is None:
            return Result.error(message="Brief não encontrado")
        return Result.success(message="Brief encontrado", data=brief)

    def identify_missing_information(self, brief: object) -> Result:
        validation = self.validate_brief(brief)
        if not validation.is_success:
            return validation
        return Result.success(
            message="Informações ausentes identificadas",
            data=missing_information(validation.data),
        )

    def build_proposal(
        self,
        *,
        brief: RemodelingBrief,
        raw_response: str,
        provider_id: str,
        routing_reason: str,
        alternatives: tuple[str, ...] = (),
    ) -> Result:
        missing = self.identify_missing_information(brief)
        if not missing.is_success:
            return missing
        try:
            proposal = parse_proposal(
                raw_response,
                brief_id=brief.id,
                provider_id=provider_id,
                routing_reason=routing_reason,
                alternatives=tuple(alternatives),
                missing_information=missing.data,
            )
        except (TypeError, ValueError) as error:
            return Result.error(message=f"Resposta incompatível: {error}")
        with self._lock:
            self._proposals[proposal.id] = proposal
        return Result.success(message="Proposta gerada para revisão", data=proposal)

    def get_proposal(self, proposal_id: str | None) -> Result:
        with self._lock:
            proposal = self._proposals.get(proposal_id or "")
        if proposal is None:
            return Result.error(message="Proposta não encontrada")
        return Result.success(message="Proposta encontrada", data=proposal)

    def transition(self, proposal_id: str | None, target: ProposalStatus) -> Result:
        current = self.get_proposal(proposal_id)
        if not current.is_success:
            return current
        allowed = {
            ProposalStatus.GENERATED: {ProposalStatus.REVIEWED, ProposalStatus.REJECTED},
            ProposalStatus.REVIEWED: {ProposalStatus.APPROVED, ProposalStatus.REJECTED},
            ProposalStatus.APPROVED: {ProposalStatus.APPLIED, ProposalStatus.REJECTED},
        }
        if target not in allowed.get(current.data.status, set()):
            return Result.error(
                message=(
                    f"Transição inválida: {current.data.status.value} → "
                    f"{target.value}"
                )
            )
        updated = replace(current.data, status=target)
        with self._lock:
            self._proposals[updated.id] = updated
        messages = {
            ProposalStatus.REVIEWED: "Proposta revisada",
            ProposalStatus.APPROVED: "Proposta aprovada",
            ProposalStatus.APPLIED: "Proposta aplicada",
            ProposalStatus.REJECTED: "Proposta rejeitada",
        }
        return Result.success(message=messages[target], data=updated)

    def list_briefs(self) -> tuple[RemodelingBrief, ...]:
        with self._lock:
            return tuple(self._briefs.values())

    def list_proposals(self):
        with self._lock:
            return tuple(self._proposals.values())
