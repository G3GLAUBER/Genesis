from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid


class EventType(Enum):
    NEW_CONVERSATION = "new_conversation"
    NEW_MESSAGE = "new_message"
    NEW_MEMORY = "new_memory"
    NEW_IDEA = "new_idea"
    NEW_DECISION = "new_decision"
    NEW_TASK = "new_task"
    NEW_DOCUMENT = "new_document"
    NEW_CODE = "new_code"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"


@dataclass
class Event:
    event_type: EventType
    data: Any

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)