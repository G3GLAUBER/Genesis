from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from Core.configuration import Configuration


def test_default_configuration():
    config = Configuration.default()

    assert config.system_name == "Gênesis"
    assert config.version == "0.1"
    assert config.environment == "development"
    assert config.minimum_python_version == (3, 12)
    assert isinstance(config.data_directory, Path)
    assert isinstance(config.logs_directory, Path)


def test_default_directories_are_inside_project():
    config = Configuration.default()
    project_root = Path(__file__).resolve().parent.parent

    assert config.data_directory == project_root / "Data"
    assert config.logs_directory == project_root / "Logs"


def test_configuration_is_immutable():
    config = Configuration.default()

    with pytest.raises(FrozenInstanceError):
        config.version = "0.2"
