"""Macro domain enums."""
from enum import Enum


class MacroIndicatorType(str, Enum):
    INFLATION = "inflation"
    INTEREST_RATE = "interest_rate"
    GDP = "gdp"
    UNEMPLOYMENT = "unemployment"
    OTHER = "other"
