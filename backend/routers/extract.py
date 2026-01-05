"""
Extract router - handles file upload and nutrition extraction.
"""

import base64
import time
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from models.nutrition import ExtractRequest, ExtractResponse
from services.file_parser import FileParser
from services.llm_extractor import LLMExtractor
from services.unit_converter import UnitConverter
from logging_config import get_logger
from config import settings
from errors import AppException, ErrorCode

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["extract"])

# Rate limiter for expensive LLM operations
# Toggle via RATE_LIMIT_ENABLED env var (default: False for development)
limiter = Limiter(key_func=get_remote_address, enabled=settings.rate_limit_enabled)


def validate_file_size(file_content_base64: str, filename: str) -> None:
    """
    Validate that the decoded file size is within limits.

    Raises:
        AppException: If file exceeds maximum allowed size
    """
    try:
        decoded = base64.b64decode(file_content_base64)
        file_size = len(decoded)
        max_size = settings.max_file_size_bytes

        if file_size > max_size:
            raise AppException(
                error_code=ErrorCode.FILE_TOO_LARGE,
                message=f"File '{filename}' exceeds maximum size of {settings.max_file_size_mb}MB",
                status_code=413
            )
    except base64.binascii.Error:
        raise AppException(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Invalid base64-encoded file content",
            status_code=400
        )


@router.post("/extract", response_model=ExtractResponse)
@limiter.limit("10/minute")  # Strict limit: 10 extractions per minute per IP
async def extract_nutrition(request: ExtractRequest, http_request: Request) -> ExtractResponse:
    """
    Extract nutrition data from an uploaded file.

    Accepts PDF, image, or text files encoded in base64.
    Uses GPT-4o Vision for PDFs and images to preserve table structure.

    Rate limited to 10 requests per minute per IP address.
    """
    start_time = time.time()

    # Validate file size before processing
    validate_file_size(request.file_content, request.filename)

    # Detect file type
    file_type = request.file_type
    if not file_type:
        file_type = FileParser.detect_file_type(request.filename)

    logger.info("Starting extraction", data={
        "filename": request.filename,
        "file_type": file_type,
        "content_length": len(request.file_content)
    })

    try:
        extractor = LLMExtractor()

        # Use vision-based extraction for PDFs and images (much more accurate for tables)
        if file_type in ("pdf", "image"):
            logger.debug("Converting file to images for vision extraction")
            images = FileParser.parse_base64_as_images(request.file_content, file_type)

            if not images:
                logger.warning("Failed to convert file to images", data={"filename": request.filename})
                return ExtractResponse(
                    success=False,
                    error="Could not convert file to images for processing."
                )

            logger.info("Sending images to GPT-4o Vision", data={"image_count": len(images)})
            product = await extractor.extract_from_images(images)
        else:
            # Text files use text-based extraction
            logger.debug("Using text-based extraction")
            text = FileParser.parse_base64(request.file_content, file_type)

            if not text.strip():
                logger.warning("No text extracted from file", data={"filename": request.filename})
                return ExtractResponse(
                    success=False,
                    error="No text could be extracted from the file."
                )

            product = await extractor.extract(text)

        # Apply unit conversions and detect anomalies
        product = UnitConverter.apply_conversions(product)

        elapsed_time = time.time() - start_time
        logger.info("Extraction completed successfully", data={
            "filename": request.filename,
            "product_name": product.product_name,
            "elapsed_seconds": round(elapsed_time, 2),
            "flags_count": len(product.flags)
        })

        return ExtractResponse(
            success=True,
            product=product
        )

    except ValueError as e:
        elapsed_time = time.time() - start_time
        logger.error("Validation error during extraction", data={
            "filename": request.filename,
            "error": str(e),
            "elapsed_seconds": round(elapsed_time, 2)
        })
        return ExtractResponse(
            success=False,
            error=str(e)
        )
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.exception("Unexpected error during extraction", data={
            "filename": request.filename,
            "error": str(e),
            "elapsed_seconds": round(elapsed_time, 2)
        })
        return ExtractResponse(
            success=False,
            error=f"An error occurred during extraction: {str(e)}"
        )
