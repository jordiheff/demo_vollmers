from pydantic import BaseModel
from typing import Optional
from .flags import ExtractionFlag


class NutritionPer100g(BaseModel):
    """Nutritional values per 100 grams of product."""
    calories: Optional[float] = None
    total_fat_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    trans_fat_g: Optional[float] = None
    cholesterol_mg: Optional[float] = None
    sodium_mg: Optional[float] = None
    total_carbohydrate_g: Optional[float] = None
    dietary_fiber_g: Optional[float] = None
    total_sugars_g: Optional[float] = None
    added_sugars_g: Optional[float] = None
    protein_g: Optional[float] = None
    vitamin_d_mcg: Optional[float] = None
    calcium_mg: Optional[float] = None
    iron_mg: Optional[float] = None
    potassium_mg: Optional[float] = None


class ExtractedProduct(BaseModel):
    """Complete extraction result from a spec sheet."""
    product_name: Optional[str] = None
    product_code: Optional[str] = None
    nutrition: NutritionPer100g
    ingredients_list: Optional[str] = None
    allergens: list[str] = []
    flags: list[ExtractionFlag] = []
    raw_text: Optional[str] = None   # Original extracted text for debugging


class ServingConfig(BaseModel):
    """User-specified serving information."""
    serving_size_g: float            # Grams per serving
    serving_size_description: str    # e.g., "1 cookie (30g)"
    servings_per_container: float    # Number of servings


class NutritionPerServing(BaseModel):
    """Calculated per-serving values with %DV."""
    serving_config: ServingConfig

    calories: Optional[float] = None
    total_fat_g: Optional[float] = None
    total_fat_dv: Optional[int] = None      # Percent daily value
    saturated_fat_g: Optional[float] = None
    saturated_fat_dv: Optional[int] = None
    trans_fat_g: Optional[float] = None     # No %DV for trans fat
    cholesterol_mg: Optional[float] = None
    cholesterol_dv: Optional[int] = None
    sodium_mg: Optional[float] = None
    sodium_dv: Optional[int] = None
    total_carbohydrate_g: Optional[float] = None
    total_carbohydrate_dv: Optional[int] = None
    dietary_fiber_g: Optional[float] = None
    dietary_fiber_dv: Optional[int] = None
    total_sugars_g: Optional[float] = None  # No %DV for total sugars
    added_sugars_g: Optional[float] = None
    added_sugars_dv: Optional[int] = None
    protein_g: Optional[float] = None       # %DV optional for protein
    vitamin_d_mcg: Optional[float] = None
    vitamin_d_dv: Optional[int] = None
    calcium_mg: Optional[float] = None
    calcium_dv: Optional[int] = None
    iron_mg: Optional[float] = None
    iron_dv: Optional[int] = None
    potassium_mg: Optional[float] = None
    potassium_dv: Optional[int] = None


# API Request/Response Models

class ExtractRequest(BaseModel):
    """Request for POST /api/extract."""
    file_content: str      # Base64-encoded file
    file_type: str         # "pdf", "image", or "text"
    filename: str          # Original filename


class ExtractResponse(BaseModel):
    """Response for POST /api/extract."""
    success: bool
    product: Optional[ExtractedProduct] = None
    error: Optional[str] = None


class CalculateRequest(BaseModel):
    """Request for POST /api/calculate."""
    nutrition: NutritionPer100g
    serving_config: ServingConfig


class CalculateResponse(BaseModel):
    """Response for POST /api/calculate."""
    success: bool
    per_serving: Optional[NutritionPerServing] = None
    error: Optional[str] = None


class LabelRequest(BaseModel):
    """Request for POST /api/label."""
    per_serving: NutritionPerServing
    product_name: Optional[str] = None
    ingredients_list: Optional[str] = None
    allergens: list[str] = []


class LabelResponse(BaseModel):
    """Response for POST /api/label."""
    success: bool
    image_base64: Optional[str] = None   # PNG image
    pdf_base64: Optional[str] = None     # PDF document
    error: Optional[str] = None
