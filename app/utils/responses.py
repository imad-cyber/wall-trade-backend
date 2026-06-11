"""
Response helper functions for consistent API responses.
"""
from typing import Any, Optional
from app.models.schemas import ResponseSchema, PaginatedResponseSchema, PaginationSchema


def success_response(
    message: str = "Operation successful",
    data: Any = None,
) -> ResponseSchema:
    """
    Create a success response.
    
    Args:
        message: Success message
        data: Response data
        
    Returns:
        ResponseSchema: Success response
    """
    return ResponseSchema(
        success=True,
        message=message,
        data=data,
    )


def error_response(
    message: str = "Operation failed",
    error_code: str = "ERROR",
    details: Optional[dict] = None,
) -> ResponseSchema:
    """
    Create an error response.
    
    Args:
        message: Error message
        error_code: Error code
        details: Error details
        
    Returns:
        ResponseSchema: Error response
    """
    return ResponseSchema(
        success=False,
        message=message,
        error={"code": error_code, "details": details},
    )


def paginated_response(
    data: list,
    page: int,
    page_size: int,
    total: int,
    message: str = "Data retrieved successfully",
) -> PaginatedResponseSchema:
    """
    Create a paginated response.
    
    Args:
        data: Data items
        page: Current page
        page_size: Page size
        total: Total items
        message: Response message
        
    Returns:
        PaginatedResponseSchema: Paginated response
    """
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponseSchema(
        success=True,
        message=message,
        data=data,
        pagination=PaginationSchema(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )
