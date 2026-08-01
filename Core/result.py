from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Result:
    is_success: bool
    message: str
    data: Any = None

    @classmethod
    def success(cls, message: str, data: Any = None) -> "Result":
        return cls(
            is_success=True,
            message=message,
            data=data,
        )

    @classmethod
    def error(cls, message: str, data: Any = None) -> "Result":
        return cls(
            is_success=False,
            message=message,
            data=data,
        )
