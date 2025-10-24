"""Core unit conversion logic used by the Tkinter GUI.

The design favours testability by keeping all arithmetic in this module so
that the GUI layer can stay thin and focus on presentation only.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Mapping


@dataclass(frozen=True)
class ConversionRule:
    """Represents a reversible conversion between a unit and a canonical unit."""

    to_base: Callable[[float], float]
    from_base: Callable[[float], float]


# Helper factory for linear conversions f(x) = x * factor
_deflinear = lambda factor: ConversionRule(
    to_base=lambda v: v * factor,
    from_base=lambda v: v / factor,
)


# Conversion tables for each supported category. For the linear categories the
# canonical unit is chosen for convenience (metre, litre, gram, kelvin second).
_LINEAR_CATEGORIES: Dict[str, Dict[str, ConversionRule]] = {
    "length": {
        "millimeter": _deflinear(0.001),
        "centimeter": _deflinear(0.01),
        "meter": _deflinear(1.0),
        "kilometer": _deflinear(1000.0),
        "inch": _deflinear(0.0254),
        "foot": _deflinear(0.3048),
        "yard": _deflinear(0.9144),
        "mile": _deflinear(1609.344),
    },
    "volume": {
        "milliliter": _deflinear(0.001),
        "liter": _deflinear(1.0),
        "cubic_meter": _deflinear(1000.0),
        "teaspoon": _deflinear(0.00492892),
        "tablespoon": _deflinear(0.0147868),
        "cup": _deflinear(0.24),
        "pint": _deflinear(0.473176),
        "gallon": _deflinear(3.78541),
    },
    "weight": {
        "milligram": _deflinear(0.001),
        "gram": _deflinear(1.0),
        "kilogram": _deflinear(1000.0),
        "ounce": _deflinear(28.3495),
        "pound": _deflinear(453.592),
        "stone": _deflinear(6350.29),
    },
    "time": {
        "microsecond": _deflinear(1e-6),
        "millisecond": _deflinear(0.001),
        "second": _deflinear(1.0),
        "minute": _deflinear(60.0),
        "hour": _deflinear(3600.0),
        "day": _deflinear(86400.0),
        "week": _deflinear(604800.0),
    },
}


def _temperature_rules() -> Dict[str, ConversionRule]:
    """Temperature conversions require affine instead of linear transformations."""

    def make_affine(to_kelvin_offset: float, scale: float) -> ConversionRule:
        return ConversionRule(
            to_base=lambda v: (v + to_kelvin_offset) * scale,
            from_base=lambda v: v / scale - to_kelvin_offset,
        )

    return {
        "celsius": ConversionRule(
            to_base=lambda v: v + 273.15,
            from_base=lambda v: v - 273.15,
        ),
        "fahrenheit": ConversionRule(
            to_base=lambda v: (v + 459.67) * 5.0 / 9.0,
            from_base=lambda v: v * 9.0 / 5.0 - 459.67,
        ),
        "kelvin": ConversionRule(
            to_base=lambda v: v,
            from_base=lambda v: v,
        ),
        "rankine": ConversionRule(
            to_base=lambda v: v * 5.0 / 9.0,
            from_base=lambda v: v * 9.0 / 5.0,
        ),
    }


_SPECIAL_CATEGORIES: Dict[str, Dict[str, ConversionRule]] = {
    "temperature": _temperature_rules(),
}


_CATEGORY_TABLES: Dict[str, Dict[str, ConversionRule]] = {
    **_LINEAR_CATEGORIES,
    **_SPECIAL_CATEGORIES,
}


class UnknownCategoryError(ValueError):
    """Raised when attempting to use an unsupported unit category."""


class UnknownUnitError(ValueError):
    """Raised when a unit is not available inside the requested category."""


def list_categories() -> Iterable[str]:
    """Return the supported conversion categories."""

    return _CATEGORY_TABLES.keys()


def list_units(category: str) -> Iterable[str]:
    """Yield the units for the provided category."""

    try:
        return _CATEGORY_TABLES[category].keys()
    except KeyError as exc:
        raise UnknownCategoryError(f"Unknown category: {category}") from exc


def convert(category: str, value: float, from_unit: str, to_unit: str) -> float:
    """Convert *value* from *from_unit* to *to_unit* within *category*.

    All arithmetic is executed in canonical space (the "base" unit).
    """

    table = _CATEGORY_TABLES.get(category)
    if table is None:
        raise UnknownCategoryError(f"Unknown category: {category}")

    from_rule = table.get(from_unit)
    if from_rule is None:
        raise UnknownUnitError(f"Unknown unit for {category}: {from_unit}")

    to_rule = table.get(to_unit)
    if to_rule is None:
        raise UnknownUnitError(f"Unknown unit for {category}: {to_unit}")

    base_value = from_rule.to_base(value)
    return to_rule.from_base(base_value)
