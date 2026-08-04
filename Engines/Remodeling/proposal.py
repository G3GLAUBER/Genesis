from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from Engines.Remodeling.budget import build_budget
from Engines.Remodeling.models import (
    ProposalStatus,
    RemodelingPhase,
    RemodelingProposal,
    SuggestedMemory,
    SuggestedMission,
)
from Engines.Remodeling.validation import required_text, text_tuple


def parse_proposal(
    raw_response: str,
    *,
    brief_id: str,
    provider_id: str,
    routing_reason: str,
    alternatives: tuple[str, ...],
    missing_information: tuple[str, ...],
) -> RemodelingProposal:
    if not isinstance(raw_response, str) or not raw_response.strip():
        raise ValueError("resposta manual deve ser texto não vazio")
    try:
        payload = json.loads(raw_response, parse_float=Decimal)
    except json.JSONDecodeError as error:
        raise ValueError(f"JSON inválido na posição {error.pos}") from error
    if not isinstance(payload, dict):
        raise ValueError("a resposta JSON deve ser um objeto")
    phases = _phases(payload.get("phases"))
    proposal_missing = text_tuple(
        payload.get("missing_information"), "missing_information"
    )
    return RemodelingProposal(
        id=str(uuid4()),
        brief_id=brief_id,
        status=ProposalStatus.GENERATED,
        phases=phases,
        risks=text_tuple(payload.get("risks"), "risks"),
        missing_information=tuple(
            dict.fromkeys((*missing_information, *proposal_missing))
        ),
        suggested_missions=_missions(payload.get("suggested_missions")),
        suggested_memories=_memories(payload.get("suggested_memories")),
        preliminary_budget=build_budget(payload.get("preliminary_budget", {})),
        assumptions=text_tuple(payload.get("assumptions"), "assumptions"),
        created_at=datetime.now(timezone.utc),
        raw_response=raw_response,
        provider_id=provider_id,
        routing_reason=routing_reason,
        alternatives=alternatives,
    )


def _phases(value: object) -> tuple[RemodelingPhase, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError("phases deve ser uma lista não vazia")
    supplied: list[tuple[dict, int, str]] = []
    orders: set[int] = set()
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("cada phase deve ser um objeto")
        order = item.get("order")
        if not isinstance(order, int) or isinstance(order, bool) or order < 1:
            raise ValueError("order de phase deve ser inteiro positivo")
        if order in orders:
            raise ValueError("ordens de phase não podem repetir")
        orders.add(order)
        supplied.append((item, order, str(uuid4())))
    ids = {order: phase_id for _, order, phase_id in supplied}
    phases: list[RemodelingPhase] = []
    for item, order, phase_id in supplied:
        dependencies = item.get("dependencies", [])
        if not isinstance(dependencies, list) or any(
            not isinstance(dep, int) or isinstance(dep, bool)
            for dep in dependencies
        ):
            raise ValueError("dependencies deve conter ordens inteiras")
        if order in dependencies or any(dep not in ids for dep in dependencies):
            raise ValueError("dependencies contém ordem inválida")
        phases.append(
            RemodelingPhase(
                id=phase_id,
                order=order,
                title=required_text(item.get("title"), "phase title"),
                description=required_text(
                    item.get("description"), "phase description"
                ),
                dependencies=tuple(ids[dep] for dep in dependencies),
                capability=required_text(
                    item.get("capability", "general_assistance"), "capability"
                ),
                estimated_duration=(
                    required_text(item["estimated_duration"], "estimated_duration")
                    if item.get("estimated_duration") is not None
                    else None
                ),
                materials=text_tuple(item.get("materials"), "materials"),
                risks=text_tuple(item.get("risks"), "phase risks"),
            )
        )
    ordered = tuple(sorted(phases, key=lambda phase: phase.order))
    _reject_cycles(ordered)
    return ordered


def _reject_cycles(phases: tuple[RemodelingPhase, ...]) -> None:
    graph = {phase.id: phase.dependencies for phase in phases}
    visited: set[str] = set()
    active: set[str] = set()

    def visit(phase_id: str) -> None:
        if phase_id in active:
            raise ValueError("dependencies contém ciclo")
        if phase_id in visited:
            return
        active.add(phase_id)
        for dependency in graph[phase_id]:
            visit(dependency)
        active.remove(phase_id)
        visited.add(phase_id)

    for phase_id in graph:
        visit(phase_id)


def _missions(value: object) -> tuple[SuggestedMission, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError("suggested_missions deve ser uma lista não vazia")
    return tuple(
        SuggestedMission(
            title=required_text(item.get("title"), "mission title"),
            objective=required_text(item.get("objective"), "mission objective"),
        )
        for item in value
        if isinstance(item, dict)
    ) if all(isinstance(item, dict) for item in value) else _invalid("suggested_missions")


def _memories(value: object) -> tuple[SuggestedMemory, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("suggested_memories deve ser uma lista")
    return tuple(
        SuggestedMemory(
            category=required_text(item.get("category"), "memory category"),
            title=required_text(item.get("title"), "memory title"),
            content=required_text(item.get("content"), "memory content"),
        )
        for item in value
        if isinstance(item, dict)
    ) if all(isinstance(item, dict) for item in value) else _invalid("suggested_memories")


def _invalid(field: str) -> tuple:
    raise ValueError(f"{field} deve conter objetos")
