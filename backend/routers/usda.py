"""
USDA router - handles ingredient search and nutrition lookup via USDA FoodData Central.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database.connection import get_db
from database.models import USDAFood
from services.usda_cache import USDAClient
from services.usda_errors import USDAAPIError
from config import settings
from logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/usda", tags=["usda"])


# ----- Response Models -----

class USDAFoodItem(BaseModel):
    """Basic food item from USDA search results."""
    fdc_id: int
    description: str
    data_type: Optional[str] = None
    brand_owner: Optional[str] = None


class USDASearchResponse(BaseModel):
    """Response from USDA food search."""
    success: bool
    query: str
    results: list[USDAFoodItem] = []
    total_hits: int = 0
    error: Optional[str] = None


class USDANutritionResponse(BaseModel):
    """Response with nutrition data for a specific food."""
    success: bool
    fdc_id: int
    description: Optional[str] = None
    nutrition: Optional[dict] = None
    error: Optional[str] = None


class CacheStatsResponse(BaseModel):
    """USDA cache performance statistics."""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    cached_foods: int
    cached_searches: int


# ----- Dependency Injection -----

def get_usda_client(db: Session = Depends(get_db)) -> USDAClient:
    """
    Dependency to get USDA client with database session.

    Raises HTTPException if USDA API is not configured.
    """
    if not settings.usda_api_key:
        raise HTTPException(
            status_code=503,
            detail="USDA API is not configured. Set USDA_API_KEY environment variable."
        )
    return USDAClient(api_key=settings.usda_api_key, db_session=db)


# ----- Endpoints -----

@router.get("/search", response_model=USDASearchResponse)
async def search_foods(
    q: str = Query(..., min_length=2, description="Search query"),
    data_types: Optional[str] = Query(
        None,
        description="Comma-separated data types: Foundation,SR Legacy,Branded,Survey"
    ),
    page_size: int = Query(25, ge=1, le=100, description="Results per page"),
    usda_client: USDAClient = Depends(get_usda_client)
) -> USDASearchResponse:
    """
    Search for foods in the USDA FoodData Central database.

    Results are cached for 90 days to minimize API calls.

    Data types:
    - Foundation: High-quality data for common foods
    - SR Legacy: Standard Reference legacy data
    - Branded: Commercial branded products
    - Survey: FNDDS (What We Eat in America)
    """
    logger.info("USDA search request", data={"query": q, "page_size": page_size})

    try:
        # Parse data types if provided
        type_list = None
        if data_types:
            type_list = [t.strip() for t in data_types.split(",")]

        results = await usda_client.search(
            query=q,
            data_types=type_list,
            page_size=page_size
        )

        logger.info("USDA search completed", data={
            "query": q,
            "result_count": len(results)
        })

        return USDASearchResponse(
            success=True,
            query=q,
            results=[USDAFoodItem(**r) for r in results],
            total_hits=len(results)
        )

    except USDAAPIError as e:
        logger.error("USDA API error during search", data={
            "query": q,
            "error_type": e.error_type.value,
            "message": str(e)
        })
        return USDASearchResponse(
            success=False,
            query=q,
            error=str(e)
        )
    except Exception as e:
        logger.exception("Unexpected error during USDA search", data={"query": q})
        return USDASearchResponse(
            success=False,
            query=q,
            error=f"Search failed: {str(e)}"
        )


@router.get("/food/{fdc_id}", response_model=USDANutritionResponse)
async def get_food_nutrition(
    fdc_id: int,
    usda_client: USDAClient = Depends(get_usda_client)
) -> USDANutritionResponse:
    """
    Get nutrition data for a specific food by FDC ID.

    Returns nutrition values per 100g in our standard format.
    Results are cached for 90 days.
    """
    logger.info("USDA food lookup", data={"fdc_id": fdc_id})

    try:
        nutrition = await usda_client.get_nutrition(fdc_id)

        if nutrition is None:
            logger.warning("Food not found in USDA", data={"fdc_id": fdc_id})
            return USDANutritionResponse(
                success=False,
                fdc_id=fdc_id,
                error=f"Food with FDC ID {fdc_id} not found"
            )

        # Get food description from cache
        food = usda_client.db.query(USDAFood).filter_by(fdc_id=fdc_id).first()

        description = food.description if food else None

        logger.info("USDA food lookup completed", data={
            "fdc_id": fdc_id,
            "description": description
        })

        return USDANutritionResponse(
            success=True,
            fdc_id=fdc_id,
            description=description,
            nutrition=nutrition.model_dump()
        )

    except USDAAPIError as e:
        logger.error("USDA API error during food lookup", data={
            "fdc_id": fdc_id,
            "error_type": e.error_type.value,
            "message": str(e)
        })
        return USDANutritionResponse(
            success=False,
            fdc_id=fdc_id,
            error=str(e)
        )
    except Exception as e:
        logger.exception("Unexpected error during USDA food lookup", data={"fdc_id": fdc_id})
        return USDANutritionResponse(
            success=False,
            fdc_id=fdc_id,
            error=f"Lookup failed: {str(e)}"
        )


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    usda_client: USDAClient = Depends(get_usda_client)
) -> CacheStatsResponse:
    """
    Get USDA cache performance statistics.

    Useful for monitoring cache efficiency and determining
    if the cache needs maintenance.
    """
    logger.debug("Cache stats requested")
    stats = usda_client.get_cache_stats()
    return CacheStatsResponse(**stats)


@router.post("/cache/clear-expired")
async def clear_expired_cache(
    usda_client: USDAClient = Depends(get_usda_client)
) -> dict:
    """
    Clear expired entries from the USDA cache.

    Removes foods and searches older than the configured expiry period
    (default 90 days).
    """
    logger.info("Clearing expired cache entries")
    usda_client.clear_expired_cache()

    # Get updated stats
    stats = usda_client.get_cache_stats()

    logger.info("Cache cleared", data={
        "remaining_foods": stats["cached_foods"],
        "remaining_searches": stats["cached_searches"]
    })

    return {
        "success": True,
        "message": "Expired cache entries cleared",
        "remaining_foods": stats["cached_foods"],
        "remaining_searches": stats["cached_searches"]
    }
