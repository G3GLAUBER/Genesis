from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Context:
    """
    Representa uma execução do Gênesis.
    """

    session_id: str
    command: str
    source: str
    timestamp: datetime

    @classmethod
    def create(
        cls,
        session_id: str,
        command: str,
        source: str,
    ) -> "Context":
        return cls(
            session_id=session_id,
            command=command,
            source=source,
            timestamp=datetime.now(),
        )
