"""Domain enums for company subdomain."""
from enum import Enum


class Sector(str, Enum):
    BANKING = "banking"
    ENERGY = "energy"
    CEMENT = "cement"
    TECHNOLOGY = "technology"
    OTHER = "other"


class Exchange(str, Enum):
    PSX = "PSX"
    KSE = "KSE"
