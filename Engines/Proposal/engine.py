from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from Core.result import Result
from Engines.Proposal.models import Proposal, ProposalStatus
from Engines.Proposal.validation import validate_draft_input, validate_proposal


class ProposalEngine:
    """Create and validate Proposal drafts without side effects."""

    def create_draft(
        self,
        *,
        workspace_id: str,
        title: str,
        objective: str,
        project_id: str | None = None,
        mission_id: str | None = None,
    ) -> Result:
        input_error = validate_draft_input(
            workspace_id=workspace_id,
            title=title,
            objective=objective,
            project_id=project_id,
            mission_id=mission_id,
        )
        if input_error:
            return Result.error(message=input_error)

        proposal = Proposal(
            id=str(uuid4()),
            version=1,
            created_at=datetime.now(timezone.utc),
            workspace_id=workspace_id,
            project_id=project_id,
            mission_id=mission_id,
            title=title,
            objective=objective,
            status=ProposalStatus.DRAFT,
        )
        proposal_error = validate_proposal(proposal)
        if proposal_error:
            return Result.error(message=proposal_error)
        return Result.success(message="Proposal DRAFT criada", data=proposal)


__all__ = ["ProposalEngine"]
