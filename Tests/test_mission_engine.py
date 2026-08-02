from dataclasses import FrozenInstanceError
from datetime import datetime
from uuid import UUID

import pytest

from Core.result import Result
from Engines.Mission import Mission, MissionEngine, MissionStatus


def create_mission_result() -> Result:
    return MissionEngine().create(
        title="  Criar renda adicional  ",
        objective=" Aumentar a renda mensal em 1000 euros ",
        constraints=[" 10 horas por semana "],
        success_criteria=[" atingir 1000 euros mensais "],
        source=" CLI ",
    )


def test_creates_valid_normalized_mission():
    mission = create_mission_result().data

    assert mission.title == "Criar renda adicional"
    assert mission.objective == "Aumentar a renda mensal em 1000 euros"
    assert mission.constraints == ("10 horas por semana",)
    assert mission.success_criteria == ("atingir 1000 euros mensais",)


@pytest.mark.parametrize("field", ["title", "objective", "source"])
def test_rejects_missing_required_fields(field):
    values = {
        "title": "Título",
        "objective": "Objetivo",
        "source": "CLI",
    }
    values[field] = "   "

    result = MissionEngine().create(**values)

    assert result.is_success is False
    assert field in result.message


def test_omitted_required_fields_return_error_result():
    result = MissionEngine().create()

    assert result.is_success is False
    assert "title" in result.message


def test_mission_id_is_unique_and_valid_uuid():
    first = create_mission_result().data
    second = create_mission_result().data

    assert first.id != second.id
    assert str(UUID(first.id)) == first.id
    assert str(UUID(second.id)) == second.id


def test_mission_timestamp_is_valid_and_timezone_aware():
    mission = create_mission_result().data

    assert isinstance(mission.created_at, datetime)
    assert mission.created_at.tzinfo is not None
    assert mission.created_at.utcoffset() is not None


def test_mission_is_immutable():
    mission = create_mission_result().data

    with pytest.raises(FrozenInstanceError):
        mission.title = "Outro título"


def test_constraints_are_immutable():
    mission = create_mission_result().data

    assert isinstance(mission.constraints, tuple)
    with pytest.raises(TypeError):
        mission.constraints[0] = "Outra restrição"


def test_success_criteria_are_immutable():
    mission = create_mission_result().data

    assert isinstance(mission.success_criteria, tuple)
    with pytest.raises(TypeError):
        mission.success_criteria[0] = "Outro critério"


def test_initial_status_is_draft():
    assert create_mission_result().data.status is MissionStatus.DRAFT


def test_source_is_preserved_after_normalization():
    assert create_mission_result().data.source == "CLI"


def test_success_result_contains_mission():
    result = create_mission_result()

    assert isinstance(result, Result)
    assert result.is_success is True
    assert isinstance(result.data, Mission)


def test_invalid_collection_returns_error_result():
    result = MissionEngine().create(
        title="Título",
        objective="Objetivo",
        constraints=("válida", " "),
        source="CLI",
    )

    assert isinstance(result, Result)
    assert result.is_success is False
    assert result.data is None
