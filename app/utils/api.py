"""
API request/response utilities.
"""
from typing import Any, Optional
from pydantic import BaseModel


class APIRequest(BaseModel):
    """Base API request model."""

    class Config:
        extra = "allow"


class APIResponse(BaseModel):
    """Base API response model."""

    status_code: int
    message: str
    data: Optional[Any] = None

    class Config:
        extra = "allow"


def format_request(data: dict) -> dict:
    """
    Format and validate API request data.
    
    Args:
        data: Request data
        
    Returns:
        dict: Formatted request data
    """
    return {k: v for k, v in data.items() if v is not None}


def format_response(
    status_code: int,
    message: str,
    data: Optional[Any] = None,
) -> dict:
    """
    Format API response.
    
    Args:
        status_code: HTTP status code
        message: Response message
        data: Response data
        
    Returns:
        dict: Formatted response
    """
    return {
        "status_code": status_code,
        "message": message,
        "data": data,
    }
