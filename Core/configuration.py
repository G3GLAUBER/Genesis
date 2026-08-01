from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Configuration:
    """
    Configuração central do Projeto Gênesis.
    """

    system_name: str
    version: str
    environment: str
    minimum_python_version: tuple[int, int]
    data_directory: Path
    logs_directory: Path

    @classmethod
    def default(cls) -> "Configuration":
        project_root = Path(__file__).resolve().parent.parent

        return cls(
            system_name="Gênesis",
            version="0.1",
            environment="development",
            minimum_python_version=(3, 12),
            data_directory=project_root / "Data",
            logs_directory=project_root / "Logs",
        )
