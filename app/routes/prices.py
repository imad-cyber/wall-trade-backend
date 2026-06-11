"""
Prices/Stock prices routes.
Example route module for price data endpoints.
"""
from fastapi import APIRouter, Depends, status, Query
from app.dependencies import get_db_dependency
from app.models.schemas import ResponseSchema

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("", response_model=ResponseSchema, status_code=status.HTTP_200_OK)
async def get_prices(
    symbol: str = Query(..., description="Stock symbol"),
    db=Depends(get_db_dependency),
):
    """
    Get stock prices.
    
    Args:
        symbol: Stock symbol
        db: Database client dependency
        
    Returns:
        ResponseSchema: Price data
    """
    # TODO: Implement price retrieval logic
    return ResponseSchema(
        success=True,
        message="Prices retrieved successfully",
        data={},
    )
