from dataclasses import dataclass, field
from datetime import datetime
from typing import List
import uuid


@dataclass
class MemoryRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    title: str = ""

    content: str = ""

    source: str = ""

    author: str = ""

    tags: List[str] = field(default_factory=list)

    importance: int = 5

    created_at: datetime = field(default_factory=datetime.now)

    updated_at: datetime = field(default_factory=datetime.now)