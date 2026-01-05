"""
Label router - handles nutrition label generation.
"""

import time
from fastapi import APIRouter

from models.nutrition import LabelRequest, LabelResponse
from services.label_generator import LabelGenerator
from logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["label"])


@router.post("/label", response_model=LabelResponse)
async def generate_label(request: LabelRequest) -> LabelResponse:
    """
    Generate FDA 2020 compliant nutrition label.

    Returns both PNG image and PDF document as base64-encoded strings.
    """
    start_time = time.time()

    logger.info("Starting label generation", data={
        "product_name": request.product_name,
        "has_ingredients": bool(request.ingredients_list),
        "allergens_count": len(request.allergens)
    })

    try:
        # Generate label
        generator = LabelGenerator()
        png_base64, pdf_base64 = generator.generate(
            request.per_serving,
            request.product_name
        )

        elapsed_time = time.time() - start_time
        logger.info("Label generation completed", data={
            "product_name": request.product_name,
            "png_size_bytes": len(png_base64),
            "pdf_size_bytes": len(pdf_base64),
            "elapsed_seconds": round(elapsed_time, 2)
        })

        return LabelResponse(
            success=True,
            image_base64=png_base64,
            pdf_base64=pdf_base64
        )

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.exception("Label generation error", data={
            "product_name": request.product_name,
            "error": str(e),
            "elapsed_seconds": round(elapsed_time, 2)
        })
        return LabelResponse(
            success=False,
            error=f"Label generation error: {str(e)}"
        )
