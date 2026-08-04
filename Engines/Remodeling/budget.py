from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from Engines.Remodeling.models import BudgetLineItem, PreliminaryBudget
from Engines.Remodeling.validation import decimal_value, required_text, text_tuple


_CENT = Decimal("0.01")


def build_budget(payload: object) -> PreliminaryBudget:
    if not isinstance(payload, dict):
        raise ValueError("preliminary_budget deve ser um objeto")
    currency = payload.get("currency", "EUR")
    if currency != "EUR":
        raise ValueError("currency deve ser EUR nesta versão")
    supplied = payload.get("line_items", [])
    if not isinstance(supplied, list):
        raise ValueError("line_items deve ser uma lista")
    items = tuple(_line_item(item) for item in supplied)
    subtotal = sum(
        (item.total for item in items if item.total is not None),
        Decimal("0"),
    ).quantize(_CENT, rounding=ROUND_HALF_UP)
    rate = decimal_value(payload.get("contingency_rate", 0), "contingency_rate")
    if rate is None:
        rate = Decimal("0")
    if rate > 1:
        raise ValueError("contingency_rate deve estar entre 0 e 1")
    contingency = (subtotal * rate).quantize(_CENT, rounding=ROUND_HALF_UP)
    return PreliminaryBudget(
        currency="EUR",
        line_items=items,
        subtotal=subtotal,
        contingency=contingency,
        total=(subtotal + contingency).quantize(_CENT),
        assumptions=text_tuple(payload.get("assumptions"), "budget assumptions"),
        confidence_level=required_text(
            payload.get("confidence_level", "low"), "confidence_level"
        ),
    )


def _line_item(payload: object) -> BudgetLineItem:
    if not isinstance(payload, dict):
        raise ValueError("cada line_item deve ser um objeto")
    quantity = decimal_value(payload.get("quantity"), "quantity")
    unit_price = decimal_value(payload.get("unit_price"), "unit_price")
    supplied_total = decimal_value(payload.get("total"), "total")
    total = supplied_total
    if quantity is not None and unit_price is not None:
        total = (quantity * unit_price).quantize(_CENT, rounding=ROUND_HALF_UP)
    unit = payload.get("unit")
    if unit is not None:
        unit = required_text(unit, "unit")
    return BudgetLineItem(
        category=required_text(payload.get("category"), "category"),
        description=required_text(payload.get("description"), "description"),
        quantity=quantity,
        unit=unit,
        unit_price=unit_price,
        total=total,
        source=required_text(payload.get("source", "manual_ai"), "source"),
        is_estimate=True,
    )
