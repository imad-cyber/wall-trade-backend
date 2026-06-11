"""
Base schemas for Pydantic models.
Provides common fields and configuration for all data models.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base Pydantic schema with common configuration."""

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        json_schema_extra={
            "example": {},
        },
    )


class TimestampedSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: datetime 
    updated_at: datetime = None

    class Config:
        """Pydantic config."""
        from_attributes = True


class ResponseSchema(BaseSchema):
    """Standard API response schema."""

    success: bool
    message: str
    data: dict = None
    error: dict = None


class PaginationSchema(BaseSchema):
    """Pagination metadata schema."""

    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponseSchema(ResponseSchema):
    """Paginated response schema."""

    pagination: PaginationSchema = None
