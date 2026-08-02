from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from uuid import uuid4

from Core.result import Result
from Engines.Mission import Mission
from Engines.Planning.models import Plan, PlanStatus, PlanStep, StepStatus


class Planner:
    def create_plan(
        self,
        *,
        mission: Mission,
        steps: Iterable[PlanStep],
    ) -> Result:
        try:
            validated_steps = self._validate_steps(steps)
        except (TypeError, ValueError) as error:
            return Result.error(message=f"Plano inválido: {error}")

        if not isinstance(mission, Mission):
            return Result.error(
                message="Plano inválido: mission deve ser uma Mission"
            )

        plan = Plan(
            id=str(uuid4()),
            mission_id=mission.id,
            status=PlanStatus.READY,
            created_at=datetime.now(timezone.utc),
            steps=validated_steps,
        )
        return Result.success(message="Plano criado", data=plan)

    @classmethod
    def _validate_steps(
        cls,
        steps: Iterable[PlanStep],
    ) -> tuple[PlanStep, ...]:
        try:
            supplied_steps = tuple(steps)
        except TypeError as error:
            raise ValueError("steps deve ser uma coleção de PlanStep") from error

        if not supplied_steps:
            raise ValueError("steps não pode ser vazio")
        if any(not isinstance(step, PlanStep) for step in supplied_steps):
            raise ValueError("todos os itens devem ser PlanStep")

        ids: set[str] = set()
        orders: set[int] = set()
        for step in supplied_steps:
            cls._validate_step(step)
            if step.id in ids:
                raise ValueError(f"id de etapa duplicado: {step.id}")
            if step.order in orders:
                raise ValueError(f"ordem de etapa duplicada: {step.order}")
            ids.add(step.id)
            orders.add(step.order)

        for step in supplied_steps:
            for dependency in step.dependencies:
                if dependency not in ids:
                    raise ValueError(
                        f"dependência inexistente: {dependency}"
                    )

        cls._reject_dependency_cycles(supplied_steps)
        return tuple(sorted(supplied_steps, key=lambda step: step.order))

    @staticmethod
    def _validate_step(step: PlanStep) -> None:
        if not isinstance(step.id, str) or not step.id.strip():
            raise ValueError("id da etapa deve ser um texto não vazio")
        if not isinstance(step.title, str) or not step.title.strip():
            raise ValueError("title da etapa deve ser um texto não vazio")
        if not isinstance(step.description, str) or not step.description.strip():
            raise ValueError("description da etapa deve ser um texto não vazio")
        if (
            not isinstance(step.order, int)
            or isinstance(step.order, bool)
            or step.order < 1
        ):
            raise ValueError("order da etapa deve ser um inteiro positivo")
        if not isinstance(step.status, StepStatus):
            raise ValueError("status da etapa deve ser StepStatus")
        if any(
            not isinstance(dependency, str) or not dependency.strip()
            for dependency in step.dependencies
        ):
            raise ValueError("dependencies deve conter IDs não vazios")
        if step.capability is not None and (
            not isinstance(step.capability, str)
            or not step.capability.strip()
        ):
            raise ValueError("capability deve ser texto não vazio")

    @staticmethod
    def _reject_dependency_cycles(steps: tuple[PlanStep, ...]) -> None:
        dependencies = {step.id: step.dependencies for step in steps}
        visited: set[str] = set()
        active: set[str] = set()

        def visit(step_id: str) -> None:
            if step_id in active:
                raise ValueError("dependências circulares não são permitidas")
            if step_id in visited:
                return

            active.add(step_id)
            for dependency in dependencies[step_id]:
                visit(dependency)
            active.remove(step_id)
            visited.add(step_id)

        for step_id in dependencies:
            visit(step_id)
