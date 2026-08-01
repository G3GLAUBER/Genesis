import pytest

from Core.registry import Registry


def test_register_and_get_module():
    registry = Registry()
    module = object()

    registry.register("MemoryEngine", module)

    assert registry.get("MemoryEngine") is module


def test_list_registered_modules():
    registry = Registry()

    registry.register("MemoryEngine", object())
    registry.register("KnowledgeEngine", object())

    assert registry.list() == [
        "MemoryEngine",
        "KnowledgeEngine",
    ]


def test_duplicate_module_raises_error():
    registry = Registry()
    module = object()

    registry.register("MemoryEngine", module)

    with pytest.raises(ValueError, match="Módulo já registrado"):
        registry.register("MemoryEngine", module)


def test_missing_module_raises_error():
    registry = Registry()

    with pytest.raises(ValueError, match="Módulo não encontrado"):
        registry.get("Inexistente")
