from dataclasses import fields

import pytest

from Core.lifecycle import Lifecycle, LifecycleState


TRANSITION_METHODS = {
    "initialize": LifecycleState.INITIALIZING,
    "ready": LifecycleState.READY,
    "start": LifecycleState.RUNNING,
    "stop": LifecycleState.STOPPING,
    "stopped": LifecycleState.STOPPED,
}

VALID_TRANSITIONS = {
    LifecycleState.BOOT: LifecycleState.INITIALIZING,
    LifecycleState.INITIALIZING: LifecycleState.READY,
    LifecycleState.READY: LifecycleState.RUNNING,
    LifecycleState.RUNNING: LifecycleState.STOPPING,
    LifecycleState.STOPPING: LifecycleState.STOPPED,
}

INVALID_TRANSITIONS = [
    (state, method_name, target)
    for state in LifecycleState
    for method_name, target in TRANSITION_METHODS.items()
    if VALID_TRANSITIONS.get(state) is not target
]


def test_initial_state_is_boot():
    lifecycle = Lifecycle()

    assert lifecycle.state is LifecycleState.BOOT


def test_state_remains_the_only_dataclass_field():
    assert [field.name for field in fields(Lifecycle)] == ["state"]


def test_lifecycle_valid_complete_flow():
    lifecycle = Lifecycle()

    lifecycle.initialize()
    assert lifecycle.state is LifecycleState.INITIALIZING

    lifecycle.ready()
    assert lifecycle.state is LifecycleState.READY

    lifecycle.start()
    assert lifecycle.state is LifecycleState.RUNNING

    lifecycle.stop()
    assert lifecycle.state is LifecycleState.STOPPING

    lifecycle.stopped()
    assert lifecycle.state is LifecycleState.STOPPED


@pytest.mark.parametrize(
    ("state", "method_name", "target"),
    INVALID_TRANSITIONS,
)
def test_invalid_transition_raises_error_and_preserves_state(
    state,
    method_name,
    target,
):
    lifecycle = Lifecycle(state=state)

    with pytest.raises(
        ValueError,
        match=rf"{state.name} -> {target.name}",
    ):
        getattr(lifecycle, method_name)()

    assert lifecycle.state is state


@pytest.mark.parametrize("state", list(LifecycleState))
def test_lifecycle_can_fail_from_any_state(state):
    lifecycle = Lifecycle(state=state)

    lifecycle.fail()

    assert lifecycle.state is LifecycleState.ERROR


def test_state_cannot_be_assigned_directly():
    lifecycle = Lifecycle()

    with pytest.raises(AttributeError, match="somente leitura"):
        lifecycle.state = LifecycleState.READY

    assert lifecycle.state is LifecycleState.BOOT


def test_invalid_initial_state_is_rejected():
    with pytest.raises(ValueError, match="Estado inicial inválido"):
        Lifecycle(state="boot")
