from dataclasses import FrozenInstanceError

import pytest

from Core.result import Result


def test_success_result():
    result = Result.success(
        message="Tudo certo",
        data={"value": 10},
    )

    assert result.is_success is True
    assert result.message == "Tudo certo"
    assert result.data == {"value": 10}


def test_error_result():
    result = Result.error(
        message="Erro",
    )

    assert result.is_success is False
    assert result.message == "Erro"
    assert result.data is None


def test_result_is_immutable():
    result = Result.success("OK")

    with pytest.raises(FrozenInstanceError):
        result.message = "Outro valor"
