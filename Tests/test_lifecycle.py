from Core.lifecycle import Lifecycle, LifecycleState


def test_initial_state_is_boot():
    lifecycle = Lifecycle()

    assert lifecycle.state is LifecycleState.BOOT


def test_lifecycle_happy_path():
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


def test_lifecycle_can_fail():
    lifecycle = Lifecycle()

    lifecycle.fail()

    assert lifecycle.state is LifecycleState.ERROR
