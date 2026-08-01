from pathlib import Path

import pytest

import CLI.doctor as doctor_module
from CLI.doctor import (
    calculate_health_score,
    check_blueprints,
    check_directories,
    check_files,
    check_python_version,
    classify_health,
    count_tests,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_python_version_is_supported():
    assert check_python_version() is True


def test_essential_directories_exist():
    assert check_directories(PROJECT_ROOT) is True


def test_essential_files_exist():
    assert check_files(PROJECT_ROOT) is True


def test_essential_blueprints_exist():
    assert check_blueprints(PROJECT_ROOT) is True


def test_count_tests_finds_test_functions():
    assert count_tests(PROJECT_ROOT) >= 13


def test_calculate_health_score():
    checks = {
        "python": True,
        "directories": True,
        "files": True,
        "blueprints": True,
        "git": False,
        "tests": True,
    }

    assert calculate_health_score(checks) == 80


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (100, "SAUDÁVEL"),
        (80, "BOM"),
        (60, "ATENÇÃO"),
        (59, "CRÍTICO"),
    ],
)
def test_classify_health(score, expected):
    assert classify_health(score) == expected


def test_run_doctor_returns_success_result(monkeypatch):
    monkeypatch.setattr(
        doctor_module,
        "check_python_version",
        lambda: True,
    )
    monkeypatch.setattr(
        doctor_module,
        "check_directories",
        lambda project_root: True,
    )
    monkeypatch.setattr(
        doctor_module,
        "check_files",
        lambda project_root: True,
    )
    monkeypatch.setattr(
        doctor_module,
        "check_blueprints",
        lambda project_root: True,
    )
    monkeypatch.setattr(
        doctor_module,
        "check_git_status",
        lambda project_root: True,
    )
    monkeypatch.setattr(
        doctor_module,
        "check_tests",
        lambda project_root: True,
    )
    monkeypatch.setattr(
        doctor_module,
        "count_tests",
        lambda project_root: 13,
    )

    result = doctor_module.run_doctor()

    assert result.is_success is True
    assert result.message == "Sistema saudável"
    assert result.data["healthy"] is True
    assert result.data["score"] == 100
    assert result.data["classification"] == "SAUDÁVEL"
    assert result.data["test_count"] == 13
