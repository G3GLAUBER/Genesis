from typing import Any


class Registry:
    def __init__(self) -> None:
        self._modules: dict[str, Any] = {}

    def register(self, name: str, module: Any) -> None:
        if name in self._modules:
            raise ValueError(f"Módulo já registrado: {name}")

        self._modules[name] = module

    def get(self, name: str) -> Any:
        if name not in self._modules:
            raise ValueError(f"Módulo não encontrado: {name}")

        return self._modules[name]

    def list(self) -> list[str]:
        return list(self._modules.keys())
