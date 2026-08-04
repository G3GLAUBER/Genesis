from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from Engines.Remodeling.models import RemodelingBrief


def required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} deve ser texto não vazio")
    return value.strip()


def optional_text(value: object, field: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{field} deve ser texto")
    return value.strip()


def text_tuple(value: object, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        supplied: Iterable[object] = (value,)
    else:
        try:
            supplied = tuple(value)
        except TypeError as error:
            raise ValueError(f"{field} deve ser uma coleção de textos") from error
    return tuple(required_text(item, field) for item in supplied)


def decimal_value(
    value: object,
    field: str,
    *,
    positive: bool = False,
) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field} deve ser numérico")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"{field} deve ser numérico") from error
    if not number.is_finite():
        raise ValueError(f"{field} deve ser finito")
    if positive and number <= 0:
        raise ValueError(f"{field} deve ser positivo")
    if not positive and number < 0:
        raise ValueError(f"{field} não pode ser negativo")
    return number


def deadline_value(value: object) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError as error:
            raise ValueError("deadline deve usar o formato YYYY-MM-DD") from error
    raise ValueError("deadline deve ser uma data válida")


def missing_information(brief: RemodelingBrief) -> tuple[str, ...]:
    missing: list[str] = []
    if any(
        value is None
        for value in (brief.room_length, brief.room_width, brief.room_height)
    ):
        missing.append("medidas completas do espaço")
    checks = (
        ("fotograf", "fotografias do estado atual"),
        ("canaliza", "localização e estado da canalização"),
        ("parede", "estado das paredes"),
        ("pavimento", "estado do pavimento"),
        ("quadro elétrico", "estado do quadro elétrico"),
        ("ventila", "condições de ventilação"),
        ("entulho", "destino do entulho"),
    )
    context = " ".join(
        (
            brief.current_condition,
            brief.desired_result,
            brief.notes,
            *brief.constraints,
            *brief.client_preferences,
            *brief.known_materials,
        )
    ).casefold()
    for needle, label in checks:
        if needle not in context:
            missing.append(label)
    if not brief.known_materials:
        missing.append("materiais escolhidos")
    if brief.deadline is None:
        missing.append("prazo desejado")
    if brief.budget_limit is None:
        missing.append("limite orçamental")
    return tuple(missing)
