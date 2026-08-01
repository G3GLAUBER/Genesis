from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from Core.context import Context


def test_create_context():
    context = Context.create(
        session_id="session-001",
        command="doctor",
        source="CLI",
    )

    assert context.session_id == "session-001"
    assert context.command == "doctor"
    assert context.source == "CLI"
    assert isinstance(context.timestamp, datetime)


def test_context_is_immutable():
    context = Context.create(
        session_id="session-001",
        command="doctor",
        source="CLI",
    )

    with pytest.raises(FrozenInstanceError):
        context.command = "memory"


def test_context_accepts_explicit_timestamp():
    timestamp = datetime(2026, 8, 1, 22, 0, 0)

    context = Context(
        session_id="session-002",
        command="memory",
        source="API",
        timestamp=timestamp,
    )

    assert context.timestamp == timestamp
