from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(item) for item in value)
    return value


def _empty_metadata() -> Mapping[str, Any]:
    return MappingProxyType({})


@dataclass(frozen=True)
class MemoryRecord:
    id: str
    workspace_id: str
    mission_id: str | None
    category: str
    title: str
    content: str
    metadata: Mapping[str, Any] = field(default_factory=_empty_metadata)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze(dict(self.metadata)))


@dataclass(frozen=True)
class MemoryQuery:
    workspace_id: str | None
    text: str | None = ""
    mission_id: str | None = None
    category: str | None = None
    limit: int | None = None


@dataclass(frozen=True)
class MemorySearchResult:
    query: MemoryQuery
    records: tuple[MemoryRecord, ...]
    total: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "records", tuple(self.records))
