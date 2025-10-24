"""Test coverage for the conversion logic."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from unit_converter_app import converter


def test_length_conversion_km_to_miles() -> None:
    result = converter.convert("length", 5.0, "kilometer", "mile")
    assert result == pytest.approx(3.10686, rel=1e-5)


def test_temperature_conversion_celsius_to_fahrenheit() -> None:
    result = converter.convert("temperature", 100.0, "celsius", "fahrenheit")
    assert result == pytest.approx(212.0)


def test_time_conversion_minutes_to_seconds() -> None:
    result = converter.convert("time", 2.5, "minute", "second")
    assert result == 150.0


def test_same_unit_returns_input() -> None:
    value = converter.convert("weight", 42.0, "kilogram", "kilogram")
    assert value == 42.0


def test_unknown_category_raises() -> None:
    with pytest.raises(converter.UnknownCategoryError):
        converter.convert("speed", 1, "mps", "kmph")


import pytest

def test_unknown_unit_raises() -> None:
    with pytest.raises(converter.UnknownUnitError):
        converter.convert("length", 1, "parsec", "meter")
