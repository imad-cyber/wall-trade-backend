"""Market domain enums."""
from enum import Enum


class MarketDirection(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
