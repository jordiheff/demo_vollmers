"""
Recipe conversion API router.

Endpoints for parsing recipes, converting volumes to weights,
and calculating nutrition for recipes.
"""

import base64
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session
from openai import AsyncOpenAI
from slowapi import Limiter
from slowapi.util import get_remote_address

from models.recipe import (
    RecipeInput,
    RecipeNutritionResult,
    ParsedIngredient,
    VolumeUnit,
    ConversionResult,
)
from models.nutrition import NutritionPer100g
from services.recipe_parser import RecipeParser
from services.volume_converter import VolumeConverter, get_supported_ingredients
from services.recipe_calculator import RecipeCalculator, create_recipe_calculator
from services.file_parser import FileParser
from services.usda_cache import USDAClient
from database.connection import get_db
from config import settings
from errors import AppException, ErrorCode
from logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/recipe", tags=["recipe"])

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


# Request/Response Models

class ExtractRecipeFromFileRequest(BaseModel):
    """Request to extract recipe from image/PDF."""
    file_content: str = Field(..., description="Base64-encoded file content")
    file_type: str = Field(..., description="File type: 'pdf' or 'image'")
    filename: str = Field(..., description="Original filename")


class ExtractRecipeFromFileResponse(BaseModel):
    """Response with extracted and parsed recipe."""
    success: bool
    recipe: Optional[RecipeInput] = None
    nutrition_result: Optional[RecipeNutritionResult] = None
    extracted_text: Optional[str] = None  # For debugging/review
    error: Optional[str] = None


class ParseRecipeRequest(BaseModel):
    """Request to parse raw recipe text."""
    recipe_text: str = Field(..., description="Raw recipe text with ingredients")
    recipe_name: Optional[str] = Field(None, description="Optional recipe name")


class ParseRecipeResponse(BaseModel):
    """Response with parsed recipe."""
    success: bool
    recipe: Optional[RecipeInput] = None
    error: Optional[str] = None


class ConvertIngredientRequest(BaseModel):
    """Request to convert a single ingredient."""
    ingredient: str = Field(..., description="Ingredient name")
    quantity: float = Field(..., description="Numeric amount")
    unit: str = Field(..., description="Unit of measurement")


class ConvertIngredientResponse(BaseModel):
    """Response with conversion result."""
    success: bool
    result: Optional[ConversionResult] = None
    error: Optional[str] = None


class CalculateRecipeRequest(BaseModel):
    """Request to calculate nutrition for a recipe."""
    recipe: RecipeInput
    ingredient_usda_ids: Optional[dict[str, int]] = Field(
        None,
        description="Optional mapping of ingredient names to USDA FDC IDs"
    )
    yield_weight_g: Optional[float] = Field(
        None,
        description="Optional final weight after cooking (for weight loss adjustment)"
    )


class CalculateRecipeResponse(BaseModel):
    """Response with calculated nutrition."""
    success: bool
    result: Optional[RecipeNutritionResult] = None
    error: Optional[str] = None


class SupportedIngredient(BaseModel):
    """Info about a supported ingredient."""
    name: str
    has_cup: bool
    has_tbsp: bool
    has_tsp: bool
    has_whole: bool
    has_stick: bool
    notes: Optional[str] = None


class SupportedIngredientsResponse(BaseModel):
    """Response with list of supported ingredients."""
    ingredients: list[SupportedIngredient]
    count: int


# Dependency injection

def get_usda_client(db: Session = Depends(get_db)) -> Optional[USDAClient]:
    """Get USDA client if API key is configured."""
    if settings.usda_api_key:
        return USDAClient(api_key=settings.usda_api_key, db_session=db)
    return None


def get_volume_converter(
    usda_client: Optional[USDAClient] = Depends(get_usda_client)
) -> VolumeConverter:
    """Get volume converter with optional USDA client."""
    return VolumeConverter(usda_client=usda_client)


def get_recipe_parser() -> RecipeParser:
    """Get recipe parser."""
    return RecipeParser()


# Vision extraction prompt for recipes
RECIPE_EXTRACTION_PROMPT = """Extract all recipe information from this image.

Focus on:
1. Recipe name/title
2. All ingredients with their quantities and units
3. Yield information (how many servings, cookies, etc.)

Return the complete text of the recipe, especially the ingredients list.
Format the ingredients clearly, one per line.
Include any notes about ingredient preparation (e.g., "softened", "sifted").

If this is not a recipe image, respond with "NOT_A_RECIPE".
"""


# Endpoints

@router.post("/extract-from-file", response_model=ExtractRecipeFromFileResponse)
@limiter.limit("5/minute")  # Strict limit: 5 recipe extractions per minute per IP
async def extract_recipe_from_file(
    http_request: Request,
    request: ExtractRecipeFromFileRequest,
    parser: RecipeParser = Depends(get_recipe_parser),
    usda_client: Optional[USDAClient] = Depends(get_usda_client)
):
    """
    Extract recipe from an image or PDF file.

    This endpoint:
    1. Converts the file to images
    2. Uses GPT-4o Vision to extract recipe text
    3. Parses ingredients using LLM
    4. Converts volumes to grams
    5. Looks up USDA nutrition for each ingredient
    6. Calculates total recipe nutrition

    Returns the parsed recipe and calculated nutrition.
    Rate limited to 5 requests per minute per IP address.
    """
    # Validate file size before processing
    validate_file_size(request.file_content, request.filename)

    try:
        # Step 1: Convert file to images
        images = FileParser.parse_base64_as_images(
            request.file_content,
            request.file_type
        )

        if not images:
            return ExtractRecipeFromFileResponse(
                success=False,
                error="Could not process the file. Please upload a valid image or PDF."
            )

        # Step 2: Use GPT-4o Vision to extract recipe text
        client = AsyncOpenAI(api_key=settings.openai_api_key)

        # Build message content with images
        content = [{"type": "text", "text": RECIPE_EXTRACTION_PROMPT}]
        for img_base64 in images[:5]:  # Limit to first 5 pages
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_base64}",
                    "detail": "high"
                }
            })

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content}],
            max_tokens=4000,
            temperature=0.1
        )

        extracted_text = response.choices[0].message.content
        if not extracted_text:
            return ExtractRecipeFromFileResponse(
                success=False,
                error="Could not extract text from the file."
            )

        # Check if it's actually a recipe
        if "NOT_A_RECIPE" in extracted_text:
            return ExtractRecipeFromFileResponse(
                success=False,
                error="This doesn't appear to be a recipe. Please upload an image or PDF of a recipe with ingredients."
            )

        # Step 3: Parse the recipe text
        recipe = await parser.parse_recipe_text(
            recipe_text=extracted_text,
            recipe_name=None  # Will be inferred from the text
        )

        # Step 4 & 5: Calculate nutrition (converts to grams and looks up USDA)
        calculator = await create_recipe_calculator(usda_client=usda_client)
        nutrition_result = await calculator.calculate_recipe_nutrition(recipe=recipe)

        return ExtractRecipeFromFileResponse(
            success=True,
            recipe=recipe,
            nutrition_result=nutrition_result,
            extracted_text=extracted_text
        )

    except ValueError as e:
        logger.warning("Validation error in recipe extraction", data={"error": str(e)})
        return ExtractRecipeFromFileResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Failed to extract recipe", data={"filename": request.filename})
        return ExtractRecipeFromFileResponse(
            success=False,
            error="An error occurred during recipe extraction. Please try again."
        )


@router.post("/parse", response_model=ParseRecipeResponse)
@limiter.limit("10/minute")  # 10 recipe parses per minute per IP
async def parse_recipe(
    http_request: Request,
    request: ParseRecipeRequest,
    parser: RecipeParser = Depends(get_recipe_parser)
):
    """
    Parse raw recipe text into structured ingredients using LLM.

    The parser extracts ingredient names, quantities, and units from
    free-form recipe text. It handles fractions, ranges, and common
    recipe formats.

    Rate limited to 10 requests per minute per IP address.

    Example input:
    ```
    2 cups all-purpose flour
    1/2 cup butter, softened
    3 large eggs
    1 tsp vanilla extract
    ```
    """
    try:
        recipe = await parser.parse_recipe_text(
            recipe_text=request.recipe_text,
            recipe_name=request.recipe_name
        )

        return ParseRecipeResponse(success=True, recipe=recipe)

    except ValueError as e:
        logger.warning("Validation error in recipe parsing", data={"error": str(e)})
        return ParseRecipeResponse(success=False, error=str(e))
    except Exception as e:
        logger.exception("Failed to parse recipe")
        return ParseRecipeResponse(
            success=False,
            error="An error occurred while parsing the recipe. Please try again."
        )


@router.post("/convert", response_model=ConvertIngredientResponse)
async def convert_ingredient(
    request: ConvertIngredientRequest,
    converter: VolumeConverter = Depends(get_volume_converter)
):
    """
    Convert a single ingredient measurement to grams.

    Uses our curated conversion table first, then falls back to
    USDA portion data or LLM estimation if needed.
    """
    try:
        result = await converter.convert_to_grams_async(
            ingredient=request.ingredient,
            quantity=request.quantity,
            unit=request.unit
        )

        return ConvertIngredientResponse(success=True, result=result)

    except Exception as e:
        logger.exception("Conversion failed", data={
            "ingredient": request.ingredient,
            "quantity": request.quantity,
            "unit": request.unit
        })
        return ConvertIngredientResponse(
            success=False,
            error="An error occurred during conversion. Please try again."
        )


@router.post("/calculate", response_model=CalculateRecipeResponse)
async def calculate_recipe(
    request: CalculateRecipeRequest,
    usda_client: Optional[USDAClient] = Depends(get_usda_client)
):
    """
    Calculate complete nutrition for a recipe.

    This endpoint:
    1. Converts all ingredients to grams
    2. Looks up nutrition data from USDA for each ingredient
    3. Calculates total recipe nutrition
    4. Converts to per-100g for label generation

    You can optionally provide:
    - ingredient_usda_ids: Map ingredient names to specific USDA FDC IDs
    - yield_weight_g: Final weight after cooking (for cooked recipes)
    """
    try:
        calculator = await create_recipe_calculator(usda_client=usda_client)

        # Update recipe with yield weight if provided
        recipe = request.recipe
        if request.yield_weight_g:
            recipe.yield_weight_g = request.yield_weight_g

        result = await calculator.calculate_recipe_nutrition(
            recipe=recipe,
            ingredient_usda_ids=request.ingredient_usda_ids
        )

        return CalculateRecipeResponse(success=True, result=result)

    except Exception as e:
        logger.exception("Recipe calculation failed", data={
            "recipe_name": request.recipe.name if request.recipe else None
        })
        return CalculateRecipeResponse(
            success=False,
            error="An error occurred during nutrition calculation. Please try again."
        )


@router.get("/ingredients", response_model=SupportedIngredientsResponse)
async def list_supported_ingredients():
    """
    Get list of all ingredients with direct volume-to-weight conversion data.

    These ingredients have high-confidence conversion factors and don't
    require USDA lookup or LLM estimation.
    """
    ingredients = get_supported_ingredients()

    return SupportedIngredientsResponse(
        ingredients=[SupportedIngredient(**ing) for ing in ingredients],
        count=len(ingredients)
    )


@router.get("/units")
async def list_supported_units():
    """
    Get list of all supported measurement units.
    """
    return {
        "volume_units": [
            {"value": "cup", "label": "Cup", "abbreviations": ["c", "cups"]},
            {"value": "tbsp", "label": "Tablespoon", "abbreviations": ["tbsp", "tablespoon", "tablespoons", "tbs"]},
            {"value": "tsp", "label": "Teaspoon", "abbreviations": ["tsp", "teaspoon", "teaspoons", "t"]},
            {"value": "fl_oz", "label": "Fluid Ounce", "abbreviations": ["fl oz", "fl. oz."]},
            {"value": "ml", "label": "Milliliter", "abbreviations": ["ml", "milliliter"]},
            {"value": "l", "label": "Liter", "abbreviations": ["l", "liter"]},
        ],
        "weight_units": [
            {"value": "g", "label": "Gram", "abbreviations": ["g", "gram", "grams"]},
            {"value": "kg", "label": "Kilogram", "abbreviations": ["kg", "kilogram"]},
            {"value": "oz", "label": "Ounce", "abbreviations": ["oz", "ounce", "ounces"]},
            {"value": "lb", "label": "Pound", "abbreviations": ["lb", "lbs", "pound", "pounds"]},
        ],
        "count_units": [
            {"value": "whole", "label": "Whole", "abbreviations": ["whole", "each"]},
            {"value": "large", "label": "Large", "abbreviations": ["large", "lg"]},
            {"value": "medium", "label": "Medium", "abbreviations": ["medium", "med"]},
            {"value": "small", "label": "Small", "abbreviations": ["small", "sm"]},
            {"value": "piece", "label": "Piece", "abbreviations": ["piece", "pieces", "pc"]},
            {"value": "slice", "label": "Slice", "abbreviations": ["slice", "slices"]},
            {"value": "clove", "label": "Clove", "abbreviations": ["clove", "cloves"]},
            {"value": "stick", "label": "Stick", "abbreviations": ["stick", "sticks"]},
            {"value": "packet", "label": "Packet", "abbreviations": ["packet", "packets"]},
            {"value": "pinch", "label": "Pinch", "abbreviations": ["pinch"]},
            {"value": "dash", "label": "Dash", "abbreviations": ["dash"]},
        ]
    }
