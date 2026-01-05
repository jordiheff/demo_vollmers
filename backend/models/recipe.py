"""
Recipe models for volume-to-weight conversion and nutrition calculation.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class VolumeUnit(str, Enum):
    """Supported volume/count units."""
    # Volume units
    CUP = "cup"
    TABLESPOON = "tbsp"
    TEASPOON = "tsp"
    FLUID_OUNCE = "fl_oz"
    MILLILITER = "ml"
    LITER = "l"
    # Weight units (pass-through)
    GRAM = "g"
    KILOGRAM = "kg"
    OUNCE = "oz"
    POUND = "lb"
    # Count units
    WHOLE = "whole"
    LARGE = "large"
    MEDIUM = "medium"
    SMALL = "small"
    SLICE = "slice"
    PIECE = "piece"
    CLOVE = "clove"
    STICK = "stick"
    PACKET = "packet"
    PINCH = "pinch"
    DASH = "dash"


class ConversionSource(str, Enum):
    """How the volume-to-weight conversion was determined."""
    DIRECT = "direct"           # Already in grams
    CONVERSION_TABLE = "table"  # From our curated table
    USDA_PORTION = "usda"       # From USDA foodPortions data
    LLM_ESTIMATE = "estimate"   # LLM-estimated (flag for review)
    USER_PROVIDED = "user"      # User manually entered


class ConversionResult(BaseModel):
    """Result of a volume-to-weight conversion."""
    ingredient: str
    original_quantity: float
    original_unit: str
    grams: float
    source: ConversionSource
    confidence: str  # "high", "medium", "low"
    note: Optional[str] = None


class ParsedIngredient(BaseModel):
    """Single ingredient parsed from recipe text."""
    raw_text: str                           # Original text: "2 cups flour"
    name: str                               # Extracted name: "flour"
    name_normalized: Optional[str] = None   # Canonical: "all-purpose flour"
    quantity: float                         # Numeric amount: 2.0
    unit: VolumeUnit                        # Unit type: "cup"

    # After conversion
    grams: Optional[float] = None           # Weight in grams: 250.0
    conversion_source: Optional[ConversionSource] = None
    conversion_confidence: Optional[str] = None  # "high", "medium", "low"
    conversion_note: Optional[str] = None   # Any notes about conversion

    # Nutrition data
    usda_fdc_id: Optional[int] = None       # USDA food ID if matched
    nutrition_per_100g: Optional[dict] = None  # Nutrition data


class RecipeInput(BaseModel):
    """Complete recipe input from user."""
    name: str = "Untitled Recipe"           # Recipe name
    raw_text: Optional[str] = None          # Raw recipe text (for parsing)
    ingredients: list[ParsedIngredient] = []  # Parsed ingredients

    # Yield information
    total_raw_weight_g: Optional[float] = None    # Sum of ingredients
    yield_weight_g: Optional[float] = None        # After cooking (optional)
    yield_quantity: Optional[int] = None          # e.g., 24 cookies
    yield_description: Optional[str] = None       # e.g., "24 cookies"


class RecipeNutritionResult(BaseModel):
    """Calculated nutrition for entire recipe."""
    recipe_name: str
    ingredients: list[ParsedIngredient]

    # Weight summary
    total_raw_weight_g: float
    yield_weight_g: Optional[float] = None  # After cooking

    # Totals for entire recipe
    total_nutrition: dict                   # Sum of all ingredients

    # Per 100g of final product
    nutrition_per_100g: dict                # Ready for label generation

    # Flags and warnings
    flags: list[dict] = []                  # Any issues to review
