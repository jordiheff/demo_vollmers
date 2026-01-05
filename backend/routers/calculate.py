"""
Calculate router - handles per-serving nutrition calculations.
"""

from fastapi import APIRouter

from models.nutrition import CalculateRequest, CalculateResponse
from services.nutrition_calc import NutritionCalculator
from logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["calculate"])


@router.post("/calculate", response_model=CalculateResponse)
async def calculate_per_serving(request: CalculateRequest) -> CalculateResponse:
    """
    Calculate per-serving nutrition values and %DV.

    Takes per-100g nutrition data and serving configuration,
    returns calculated per-serving values with FDA-compliant rounding.
    """
    logger.info("Starting calculation", data={
        "serving_size_g": request.serving_config.serving_size_g,
        "servings_per_container": request.serving_config.servings_per_container
    })

    try:
        # Validate serving config
        if request.serving_config.serving_size_g <= 0:
            logger.warning("Invalid serving size", data={"serving_size_g": request.serving_config.serving_size_g})
            return CalculateResponse(
                success=False,
                error="Serving size must be greater than 0"
            )

        if request.serving_config.servings_per_container <= 0:
            logger.warning("Invalid servings per container", data={"servings_per_container": request.serving_config.servings_per_container})
            return CalculateResponse(
                success=False,
                error="Servings per container must be greater than 0"
            )

        # Calculate per-serving values
        per_serving = NutritionCalculator.calculate_per_serving(
            request.nutrition,
            request.serving_config
        )

        logger.info("Calculation completed", data={
            "calories_per_serving": per_serving.calories,
            "serving_description": request.serving_config.serving_size_description
        })

        return CalculateResponse(
            success=True,
            per_serving=per_serving
        )

    except Exception as e:
        logger.exception("Calculation error", data={"error": str(e)})
        return CalculateResponse(
            success=False,
            error=f"Calculation error: {str(e)}"
        )
