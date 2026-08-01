from pathlib import Path

from CLI.doctor import (
    check_directories,
    check_files,
    check_python_version,
    run_doctor,
)


def test_python_version_is_supported():
    assert check_python_version() is True


def test_essential_directories_exist():
    project_root = Path(__file__).resolve().parent.parent

    assert check_directories(project_root) is True


def test_essential_files_exist():
    project_root = Path(__file__).resolve().parent.parent

    assert check_files(project_root) is True


def test_run_doctor_returns_success_result():
    result = run_doctor()

    assert result.is_success is True
    assert result.message == "Sistema saudável"
    assert result.data == {"healthy": True}
