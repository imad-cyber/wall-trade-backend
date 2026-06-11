"""
API v1 schemas - common data models for v1 API.
Additional schema files can be created for specific endpoints.
"""
from app.models.schemas import (
    BaseSchema,
    TimestampedSchema,
    ResponseSchema,
    PaginationSchema,
    PaginatedResponseSchema,
)

__all__ = [
    "BaseSchema",
    "TimestampedSchema",
    "ResponseSchema",
    "PaginationSchema",
    "PaginatedResponseSchema",
]
