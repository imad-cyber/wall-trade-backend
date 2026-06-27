"""Auth domain enums."""
from enum import Enum


class UserRole(str, Enum):
    AUTHENTICATED = "authenticated"
    ADMIN = "admin"
    SERVICE = "service"
