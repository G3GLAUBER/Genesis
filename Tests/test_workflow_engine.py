from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
from threading import Thread
from urllib.request import urlopen

import pytest

from Application import bootstrap_application
from Core.result import Result
from Engines.Workflow import (
    WorkflowEngine,
    WorkflowObservation,
    WorkflowStage,
)
from Interfaces.Companion.application import CompanionApplication
from Interfaces.Companion.server import create_server


def _observation(**changes) -> WorkflowObservation:
    values = {
        "project_id": "project-1",
        "project_title": "Casa de Banho",
    }
    values.update(changes)
    return WorkflowObservation(**values)


def _evaluate(**changes):
    result = WorkflowEngine().evaluate(_observation(**changes))
    assert result.is_success
    return result.data


def _project(container):
    workspace_id = container.workspace_service.active_workspace_id
    created = container.project_service.create(
        workspace_id=workspace_id,
        title="Casa de Banho",
        client="Cliente",
        address="Lisboa",
        description="Substituir banheira",
    )
    assert created.is_success
    return created.data


def test_empty_workflow_list_is_safe_and_invalid_observation_is_controlled():
    container = bootstrap_application()

    listed = container.workflow_service.list_for_workspace(
        container.workspace_service.active_workspace_id
    )

    assert listed.is_success
    assert listed.data == ()
    assert not WorkflowEngine().evaluate(None).is_success


def test_new_project_recommends_first_mission():
    state = _evaluate()

    assert state.current_stage is WorkflowStage.PROJECT_CREATED
    assert state.progress == 10
    assert state.next_action == "Criar a primeira Mission"
    assert state.recommendation.destination == "/#mission-copilot"


def test_created_mission_recommends_mission_copilot():
    state = _evaluate(mission_ids=("mission-1",))

    assert state.current_stage is WorkflowStage.MISSION_CREATED
    assert state.progress == 25
    assert state.recommendation.destination == "/missions/mission-1"


def test_completed_mission_copilot_recommends_proposal():
    state = _evaluate(
        mission_ids=("mission-1",),
        mission_copilot_completed=True,
    )

    assert state.current_stage is WorkflowStage.MISSION_COMPLETED
    assert state.progress == 40
    assert state.next_action == "Gerar Proposal"


@pytest.mark.parametrize(
    ("changes", "stage", "progress", "action"),
    (
        (
            {"proposal_pending": True},
            WorkflowStage.PROPOSAL_PENDING,
            50,
            "Rever Proposal",
        ),
        (
            {"proposal_approved": True},
            WorkflowStage.PROPOSAL_APPROVED,
            60,
            "Criar Planning",
        ),
        (
            {"planning_ready": True},
            WorkflowStage.PLANNING_PENDING,
            70,
            "Iniciar Execution",
        ),
        (
            {"execution_pending": True},
            WorkflowStage.EXECUTION_PENDING,
            85,
            "Continuar Execution",
        ),
        (
            {"execution_completed": True},
            WorkflowStage.COMPLETED,
            100,
            "Rever o resultado do Project",
        ),
    ),
)
def test_stages_produce_consistent_progress_and_recommendation(
    changes,
    stage,
    progress,
    action,
):
    state = _evaluate(mission_ids=("mission-1",), **changes)

    assert state.current_stage is stage
    assert state.progress == progress
    assert state.next_action == action


def test_blocker_has_high_priority_and_is_preserved_immutably():
    state = _evaluate(blockers=("Falta aprovação.",))

    assert state.recommendation.priority == "high"
    assert state.blockers == ("Falta aprovação.",)
    with pytest.raises(FrozenInstanceError):
        state.progress = 99


def test_application_evaluates_project_and_mission_copilot_evidence():
    container = bootstrap_application()
    project = _project(container)

    initial = container.workflow_service.evaluate_project(project.id)
    assert initial.data.current_stage is WorkflowStage.PROJECT_CREATED

    request = container.mission_copilot_service.create_mission_copilot_request(
        title="Planejar substituição",
        objective="Definir sequência e riscos",
        project_id=project.id,
    )
    assert request.is_success
    with_mission = container.workflow_service.evaluate_project(project.id)
    assert with_mission.data.current_stage is WorkflowStage.MISSION_CREATED

    handoff = container.mission_copilot_service.create_handoff(
        request.data.mission.id
    )
    completed = container.mission_copilot_service.complete_handoff(
        request.data.mission.id,
        handoff.data.id,
        response='{"summary": "Plano inicial"}',
    )
    assert completed.is_success
    built = container.mission_copilot_service.build_result(
        request.data.mission.id,
        handoff.data.id,
    )
    assert built.is_success

    guided = container.workflow_service.evaluate_project(project.id)
    assert guided.data.current_stage is WorkflowStage.MISSION_COMPLETED
    assert guided.data.next_action == "Gerar Proposal"


def test_application_does_not_infer_planning_without_public_evidence():
    container = bootstrap_application()

    class CapturingEngine:
        def __init__(self):
            self.observation = None

        def evaluate(self, observation):
            self.observation = observation
            return Result.success(message="captured", data=observation)

    engine = CapturingEngine()
    service = container.workflow_service.__class__(
        engine,
        container.project_service,
        container.mission_service,
        mission_copilot_service=container.mission_copilot_service,
        remodeling_service=container.remodeling_service,
    )
    project = _project(container)

    result = service.evaluate_project(project.id)

    assert result.is_success
    assert engine.observation is not None
    assert engine.observation.planning_ready is False


def test_application_keeps_pending_execution_when_another_execution_completed():
    from dataclasses import replace
    from types import SimpleNamespace

    container = bootstrap_application()
    project = _project(container)
    project = replace(project, mission_ids=("mission-1",))

    class ProjectEvidence:
        def get(self, project_id):
            return Result.success(data=project, message="project")

    class MixedExecutionService:
        def list_executions(self, *, workspace_id=None):
            from Engines.Execution import ExecutionStatus

            completed = SimpleNamespace(
                mission=SimpleNamespace(id="mission-1"),
                report=SimpleNamespace(status=ExecutionStatus.COMPLETED),
            )
            pending = SimpleNamespace(
                mission=SimpleNamespace(id="mission-1"),
                report=SimpleNamespace(status=ExecutionStatus.RUNNING),
            )
            return Result.success(
                data=(completed, pending), message="mixed"
            )

    class CapturingEngine:
        def evaluate(self, observation):
            return Result.success(data=observation, message="captured")

    service = container.workflow_service.__class__(
        CapturingEngine(),
        ProjectEvidence(),
        MixedExecutionService(),
    )
    evaluated = service.evaluate_project(project.id)

    assert evaluated.is_success
    assert evaluated.data.execution_pending is True


def test_evaluation_never_changes_project_or_creates_mission():
    container = bootstrap_application()
    project = _project(container)

    before = container.project_service.get(project.id).data
    missions_before = container.mission_service.list_missions().data
    evaluated = container.workflow_service.evaluate_project(project.id)
    after = container.project_service.get(project.id).data
    missions_after = container.mission_service.list_missions().data

    assert evaluated.is_success
    assert before == after
    assert missions_before == missions_after == ()


def test_companion_exposes_guidance_on_command_center_and_projects_over_http():
    app = CompanionApplication.default()
    created = app.create_project(
        title="Casa de Banho",
        client="Cliente",
        address="Lisboa",
        description="Substituir banheira",
    )
    assert created.is_success
    server = create_server(host="127.0.0.1", port=0, application=app)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        with urlopen(f"http://{host}:{port}/", timeout=2) as response:
            home = response.read().decode("utf-8")
        with urlopen(f"http://{host}:{port}/projects", timeout=2) as response:
            projects = response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert "Próxima ação" in home
    assert "Criar a primeira Mission" in home
    assert "Progresso" in projects
    assert "Project criado" in projects
    assert "Criar a primeira Mission" in projects


def test_workflow_has_no_network_or_automatic_action_dependencies():
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("Engines/Workflow").glob("*.py")
    )

    assert "urlopen" not in source
    assert "requests" not in source
    assert "execute(" not in source
    assert "create_mission" not in source
