"""Common API query parameters."""
from enum import Enum

from pydantic import BaseModel, Field


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class PaginationParams(BaseModel):
    limit: int = Field(20, ge=1, le=500)
    offset: int = Field(0, ge=0)
