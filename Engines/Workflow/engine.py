from __future__ import annotations

from datetime import datetime, timezone

from Core.result import Result
from Engines.Workflow.models import (
    WorkflowObservation,
    WorkflowRecommendation,
    WorkflowStage,
    WorkflowState,
)


class WorkflowEngine:
    """Produces guidance from observed state without causing side effects."""

    def evaluate(self, observation: object) -> Result:
        if not isinstance(observation, WorkflowObservation):
            return Result.error(message="Observação de Workflow inválida")
        if not observation.project_id.strip():
            return Result.error(message="Project é obrigatório para o Workflow")

        stage, progress, title, description, destination, reason = (
            self._guidance(observation)
        )
        priority = "high" if observation.blockers else "medium"
        if stage is WorkflowStage.COMPLETED:
            priority = "low"
        recommendation = WorkflowRecommendation(
            title=title,
            description=description,
            priority=priority,
            destination=destination,
            rationale=reason,
        )
        state = WorkflowState(
            project_id=observation.project_id,
            current_stage=stage,
            progress=progress,
            next_action=title,
            recommendation=recommendation,
            reason=reason,
            blockers=observation.blockers,
            updated_at=datetime.now(timezone.utc),
        )
        return Result.success(message="Workflow avaliado", data=state)

    @staticmethod
    def _guidance(
        observation: WorkflowObservation,
    ) -> tuple[WorkflowStage, int, str, str, str, str]:
        if observation.project_completed or observation.execution_completed:
            return (
                WorkflowStage.COMPLETED,
                100,
                "Rever o resultado do Project",
                (
                    "Você concluiu esta etapa. Reveja o resultado e preserve "
                    "o aprendizado."
                ),
                "/executions",
                "O Project ou sua Execution foi concluído.",
            )
        if observation.execution_pending:
            return (
                WorkflowStage.EXECUTION_PENDING,
                85,
                "Continuar Execution",
                "A execução está preparada e ainda precisa ser concluída.",
                "/executions",
                "Há uma Execution pendente neste Project.",
            )
        if observation.planning_ready:
            return (
                WorkflowStage.PLANNING_PENDING,
                70,
                "Iniciar Execution",
                "O Planning está pronto para orientar a execução.",
                "/missions",
                "O Project já possui um Planning disponível.",
            )
        if observation.proposal_approved:
            return (
                WorkflowStage.PROPOSAL_APPROVED,
                60,
                "Criar Planning",
                "A Proposal aprovada pode agora ser transformada em Planning.",
                "/missions",
                "A Proposal já foi aprovada.",
            )
        if observation.proposal_pending:
            return (
                WorkflowStage.PROPOSAL_PENDING,
                50,
                "Rever Proposal",
                "A Proposal precisa do seu julgamento antes de avançar.",
                "/remodeling",
                "Há uma Proposal aguardando Review.",
            )
        if observation.mission_copilot_completed:
            return (
                WorkflowStage.MISSION_COMPLETED,
                40,
                "Gerar Proposal",
                (
                    "Este Project já possui contexto suficiente para preparar "
                    "uma Proposal."
                ),
                "/remodeling",
                "O Mission Copilot foi concluído.",
            )
        if observation.mission_ids:
            mission_id = observation.mission_ids[-1]
            return (
                WorkflowStage.MISSION_CREATED,
                25,
                "Continuar Mission Copilot",
                "A Mission existe e está pronta para receber orientação.",
                f"/missions/{mission_id}",
                "Há uma Mission criada para este Project.",
            )
        return (
            WorkflowStage.PROJECT_CREATED,
            10,
            "Criar a primeira Mission",
            "Agora recomendamos criar a primeira Mission.",
            "/#mission-copilot",
            "O Project ainda não possui Missions.",
        )
