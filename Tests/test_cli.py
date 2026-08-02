import sys

import pytest

import CLI.main as main_module
from Core.result import Result


def run_cli(
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    result: Result | None = None,
) -> int:
    monkeypatch.setattr(sys, "argv", ["genesis", command])

    if result is not None:
        monkeypatch.setattr(
            main_module,
            "run_doctor",
            lambda: result,
        )

    with pytest.raises(SystemExit) as exit_info:
        main_module.main()

    exit_code = exit_info.value.code
    assert isinstance(exit_code, int)
    return exit_code


def test_result_success_returns_exit_code_zero(monkeypatch):
    result = Result.success("Sistema saudável")

    assert run_cli(monkeypatch, "doctor", result) == 0


def test_result_error_returns_exit_code_one(monkeypatch):
    result = Result.error("Problemas encontrados")

    assert run_cli(monkeypatch, "doctor", result) == 1


def test_unknown_command_returns_exit_code_two(monkeypatch):
    assert run_cli(monkeypatch, "inexistente") == 2
