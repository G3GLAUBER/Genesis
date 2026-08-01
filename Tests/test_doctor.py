from pathlib import Path

from CLI.doctor import check_directories, check_files, check_python_version


def test_python_version_is_supported():
    assert check_python_version() is True


def test_essential_directories_exist():
    project_root = Path(__file__).resolve().parent.parent

    assert check_directories(project_root) is True


def test_essential_files_exist():
    project_root = Path(__file__).resolve().parent.parent

    assert check_files(project_root) is True
