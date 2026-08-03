from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from Application import MemoryService, bootstrap_application
from Core.result import Result
from Engines.Memory import (
    InMemoryRepository,
    MemoryEngine,
    MemoryQuery,
    MemoryRecord,
    MemoryRepository,
    MemorySearchResult,
)


def create_service() -> MemoryService:
    return MemoryService(MemoryEngine(InMemoryRepository()))


def store(
    service: MemoryService,
    *,
    workspace_id: str = "workspace-1",
    mission_id: str | None = None,
    category: str = "nota",
    title: str = "Decisão",
    content: str = "Usar contratos imutáveis",
    metadata=None,
):
    return service.store(
        workspace_id=workspace_id,
        mission_id=mission_id,
        category=category,
        title=title,
        content=content,
        metadata=metadata,
    )


def test_store_creates_normalized_memory_record():
    result = store(
        create_service(),
        workspace_id=" workspace-1 ",
        mission_id=" mission-1 ",
        category=" decisão técnica ",
        title=" Arquitetura ",
        content=" Application coordena Engines. ",
    )

    assert isinstance(result, Result)
    assert result.is_success is True
    assert isinstance(result.data, MemoryRecord)
    assert result.data.workspace_id == "workspace-1"
    assert result.data.mission_id == "mission-1"
    assert result.data.category == "decisão técnica"
    assert result.data.created_at.tzinfo is timezone.utc


def test_store_requires_workspace_and_accepts_free_category():
    service = create_service()

    invalid = store(service, workspace_id=" ")
    valid = store(service, category="qualquer categoria livre")

    assert invalid.is_success is False
    assert "workspace_id" in invalid.message
    assert valid.is_success is True
    assert valid.data.category == "qualquer categoria livre"


def test_search_matches_title_and_content_case_insensitively():
    service = create_service()
    store(service, title="Arquitetura Modular", content="Separação")
    store(service, title="Outra", content="Contrato de MEMÓRIA oficial")

    title_result = service.search(
        workspace_id="workspace-1",
        text="arquitetura",
    )
    content_result = service.search(
        workspace_id="workspace-1",
        text="memória",
    )

    assert title_result.data.total == 1
    assert title_result.data.records[0].title == "Arquitetura Modular"
    assert content_result.data.total == 1
    assert isinstance(content_result.data, MemorySearchResult)


def test_search_filters_category_mission_and_limit():
    service = create_service()
    store(service, mission_id="mission-1", category="decisão", title="Um")
    store(service, mission_id="mission-1", category="nota", title="Dois")
    store(service, mission_id="mission-2", category="decisão", title="Três")

    result = service.search(
        workspace_id="workspace-1",
        mission_id="mission-1",
        category="DECISÃO",
        limit=1,
    )

    assert result.data.total == 1
    assert result.data.records[0].title == "Um"


def test_history_returns_newest_first_and_filters_optional_mission():
    service = create_service()
    first = store(service, mission_id=None, title="Primeira").data
    second = store(service, mission_id="mission-1", title="Segunda").data

    history = service.history(workspace_id="workspace-1")
    mission_history = service.history(
        workspace_id="workspace-1",
        mission_id="mission-1",
    )

    assert history.data == (second, first)
    assert mission_history.data == (second,)
    assert first.mission_id is None


def test_delete_removes_only_record_from_supplied_workspace():
    service = create_service()
    record = store(service, workspace_id="workspace-1").data

    wrong_workspace = service.delete(
        workspace_id="workspace-2",
        record_id=record.id,
    )
    deleted = service.delete(
        workspace_id="workspace-1",
        record_id=record.id,
    )

    assert wrong_workspace.is_success is False
    assert deleted.is_success is True
    assert service.history(workspace_id="workspace-1").data == ()


def test_clear_removes_only_workspace_history():
    service = create_service()
    store(service, workspace_id="workspace-1", title="Um")
    store(service, workspace_id="workspace-1", title="Dois")
    other = store(service, workspace_id="workspace-2", title="Outro").data

    result = service.clear(workspace_id="workspace-1")

    assert result.data == 2
    assert service.history(workspace_id="workspace-1").data == ()
    assert service.history(workspace_id="workspace-2").data == (other,)


def test_search_and_history_are_isolated_by_workspace():
    service = create_service()
    own = store(service, workspace_id="workspace-1", title="Compartilhado").data
    store(service, workspace_id="workspace-2", title="Compartilhado")

    searched = service.search(
        workspace_id="workspace-1",
        text="compartilhado",
    )

    assert searched.data.records == (own,)
    assert service.history(workspace_id="workspace-1").data == (own,)


def test_models_and_nested_metadata_are_immutable():
    source = {"tags": ["architecture"], "details": {"version": 1}}
    record = store(create_service(), metadata=source).data
    source["tags"].append("changed")

    assert record.metadata["tags"] == ("architecture",)
    with pytest.raises(TypeError):
        record.metadata["new"] = True
    with pytest.raises(FrozenInstanceError):
        record.title = "Outro"
    with pytest.raises(FrozenInstanceError):
        MemoryQuery(workspace_id="workspace-1").text = "novo"


def test_repository_is_an_abstract_contract_and_in_memory_is_instance_local():
    with pytest.raises(TypeError):
        MemoryRepository()

    first = InMemoryRepository()
    second = InMemoryRepository()
    record = MemoryRecord(
        id="record-1",
        workspace_id="workspace-1",
        mission_id=None,
        category="nota",
        title="Registro",
        content="Conteúdo",
        created_at=datetime.now(timezone.utc),
    )
    first.store(record)

    assert first.list("workspace-1") == (record,)
    assert second.list("workspace-1") == ()


def test_application_service_delegates_to_memory_engine():
    class SpyMemoryEngine(MemoryEngine):
        def __init__(self):
            super().__init__(InMemoryRepository())
            self.calls = []

        def store(self, **kwargs):
            self.calls.append(kwargs)
            return Result.success("delegado")

    engine = SpyMemoryEngine()
    service = MemoryService(engine)

    result = store(service)

    assert result.message == "delegado"
    assert engine.calls[0]["workspace_id"] == "workspace-1"


def test_bootstrap_exposes_memory_contract_without_global_state():
    first = bootstrap_application()
    second = bootstrap_application()

    stored = store(first.memory_service).data

    assert first.memory_service._engine is first.memory_engine
    assert first.memory_engine._repository is first.memory_repository
    assert first.memory_repository is not second.memory_repository
    assert first.memory_service.history(workspace_id="workspace-1").data == (
        stored,
    )
    assert second.memory_service.history(workspace_id="workspace-1").data == ()
