"""
Recipe nutrition calculator service.

Calculates total nutrition for a recipe by:
1. Converting all ingredients to grams
2. Getting nutrition per 100g for each ingredient from USDA
3. Calculating each ingredient's contribution based on weight
4. Summing to get total recipe nutrition
5. Converting to per-100g of final product
"""

from typing import Optional
from models.recipe import (
    RecipeInput,
    RecipeNutritionResult,
    ParsedIngredient,
    ConversionSource,
)
from models.nutrition import NutritionPer100g
from services.volume_converter import VolumeConverter
from services.usda_cache import USDAClient


# Nutrients that need to be tracked and summed
TRACKED_NUTRIENTS = [
    "calories",
    "total_fat_g",
    "saturated_fat_g",
    "trans_fat_g",
    "cholesterol_mg",
    "sodium_mg",
    "total_carbohydrate_g",
    "dietary_fiber_g",
    "total_sugars_g",
    "added_sugars_g",
    "protein_g",
    "vitamin_d_mcg",
    "calcium_mg",
    "iron_mg",
    "potassium_mg",
]


class RecipeCalculator:
    """
    Calculate nutrition for an entire recipe.

    Combines volume conversion, USDA lookups, and nutrition math.
    """

    def __init__(
        self,
        volume_converter: VolumeConverter,
        usda_client: Optional[USDAClient] = None
    ):
        self.volume_converter = volume_converter
        self.usda_client = usda_client

    async def calculate_recipe_nutrition(
        self,
        recipe: RecipeInput,
        ingredient_usda_ids: Optional[dict[str, int]] = None
    ) -> RecipeNutritionResult:
        """
        Calculate complete nutrition for a recipe.

        Args:
            recipe: RecipeInput with parsed ingredients
            ingredient_usda_ids: Optional mapping of ingredient names to USDA FDC IDs
                                (if not provided, will search USDA for each ingredient)

        Returns:
            RecipeNutritionResult with total and per-100g nutrition
        """
        ingredient_usda_ids = ingredient_usda_ids or {}
        flags = []

        # Step 1: Convert all ingredients to grams
        converted_ingredients = []
        for ingredient in recipe.ingredients:
            converted = await self._convert_ingredient(ingredient)
            converted_ingredients.append(converted)

            # Flag low confidence conversions
            if converted.conversion_confidence == "low":
                flags.append({
                    "type": "low_confidence_conversion",
                    "ingredient": converted.name,
                    "message": f"Low confidence conversion for {converted.raw_text}. Please verify weight.",
                    "severity": "warning"
                })

        # Step 2: Get nutrition data for each ingredient
        for ingredient in converted_ingredients:
            if ingredient.grams and ingredient.grams > 0:
                # Use provided FDC ID or search USDA
                fdc_id = ingredient_usda_ids.get(ingredient.name)
                nutrition = await self._get_ingredient_nutrition(
                    ingredient.name,
                    ingredient.name_normalized or ingredient.name,
                    fdc_id
                )

                if nutrition:
                    ingredient.nutrition_per_100g = nutrition.model_dump()
                    ingredient.usda_fdc_id = fdc_id
                else:
                    flags.append({
                        "type": "missing_nutrition",
                        "ingredient": ingredient.name,
                        "message": f"Could not find nutrition data for {ingredient.name}. Using zeros.",
                        "severity": "warning"
                    })

        # Step 3: Calculate total raw weight
        total_raw_weight_g = sum(
            ing.grams for ing in converted_ingredients
            if ing.grams is not None
        )

        if total_raw_weight_g == 0:
            flags.append({
                "type": "no_weight",
                "message": "Could not calculate total weight. All conversions failed.",
                "severity": "error"
            })

        # Step 4: Calculate total nutrition by summing contributions
        total_nutrition = self._calculate_total_nutrition(
            converted_ingredients,
            total_raw_weight_g
        )

        # Step 5: Convert to per-100g
        yield_weight = recipe.yield_weight_g or total_raw_weight_g
        nutrition_per_100g = self._calculate_per_100g(
            total_nutrition,
            yield_weight
        )

        # Flag if using raw weight instead of yield weight
        if recipe.yield_weight_g is None:
            flags.append({
                "type": "no_yield_weight",
                "message": "Using raw ingredient weight as final weight. Consider providing cooked/final weight for accuracy.",
                "severity": "info"
            })

        return RecipeNutritionResult(
            recipe_name=recipe.name,
            ingredients=converted_ingredients,
            total_raw_weight_g=total_raw_weight_g,
            yield_weight_g=yield_weight,
            total_nutrition=total_nutrition,
            nutrition_per_100g=nutrition_per_100g,
            flags=flags
        )

    async def _convert_ingredient(
        self,
        ingredient: ParsedIngredient
    ) -> ParsedIngredient:
        """Convert a single ingredient to grams."""
        result = await self.volume_converter.convert_to_grams_async(
            ingredient=ingredient.name,
            quantity=ingredient.quantity,
            unit=ingredient.unit.value
        )

        # Update ingredient with conversion result
        ingredient.name_normalized = result.ingredient
        ingredient.grams = result.grams
        ingredient.conversion_source = result.source
        ingredient.conversion_confidence = result.confidence
        ingredient.conversion_note = result.note

        return ingredient

    async def _get_ingredient_nutrition(
        self,
        name: str,
        normalized_name: str,
        fdc_id: Optional[int] = None
    ) -> Optional[NutritionPer100g]:
        """Get nutrition data for an ingredient from USDA."""
        if not self.usda_client:
            return None

        try:
            # If we have a specific FDC ID, use it
            if fdc_id:
                return await self.usda_client.get_nutrition(fdc_id)

            # Otherwise search USDA
            # Try normalized name first, then original name
            for search_term in [normalized_name, name]:
                results = await self.usda_client.search(
                    search_term,
                    data_types=["Foundation", "SR Legacy"],
                    page_size=5
                )

                if results:
                    # Use the first result (best match)
                    fdc_id = results[0]["fdc_id"]
                    return await self.usda_client.get_nutrition(fdc_id)

            return None

        except Exception:
            return None

    def _calculate_total_nutrition(
        self,
        ingredients: list[ParsedIngredient],
        total_weight_g: float
    ) -> dict:
        """
        Sum nutrition from all ingredients.

        Each ingredient's contribution is:
        (ingredient_grams / 100) * nutrient_per_100g
        """
        totals = {nutrient: 0.0 for nutrient in TRACKED_NUTRIENTS}

        for ingredient in ingredients:
            if not ingredient.grams or ingredient.grams <= 0:
                continue

            if not ingredient.nutrition_per_100g:
                continue

            # Calculate this ingredient's contribution
            factor = ingredient.grams / 100.0

            for nutrient in TRACKED_NUTRIENTS:
                value = ingredient.nutrition_per_100g.get(nutrient)
                if value is not None:
                    totals[nutrient] += value * factor

        return totals

    def _calculate_per_100g(
        self,
        total_nutrition: dict,
        yield_weight_g: float
    ) -> dict:
        """
        Convert total nutrition to per-100g values.

        Formula: nutrient_per_100g = (total_nutrient / yield_weight) * 100
        """
        if yield_weight_g <= 0:
            return {nutrient: 0.0 for nutrient in TRACKED_NUTRIENTS}

        per_100g = {}
        for nutrient, total_value in total_nutrition.items():
            per_100g[nutrient] = (total_value / yield_weight_g) * 100

        return per_100g

    def calculate_ingredient_contribution(
        self,
        ingredient: ParsedIngredient,
        total_weight_g: float
    ) -> dict:
        """
        Calculate what percentage and absolute values an ingredient contributes.

        Useful for showing users which ingredients contribute most to each nutrient.
        """
        if not ingredient.grams or ingredient.grams <= 0:
            return {
                "weight_percent": 0,
                "nutrients": {}
            }

        weight_percent = (ingredient.grams / total_weight_g) * 100 if total_weight_g > 0 else 0

        nutrient_contributions = {}
        if ingredient.nutrition_per_100g:
            factor = ingredient.grams / 100.0
            for nutrient in TRACKED_NUTRIENTS:
                value = ingredient.nutrition_per_100g.get(nutrient)
                if value is not None:
                    nutrient_contributions[nutrient] = value * factor

        return {
            "weight_percent": round(weight_percent, 1),
            "nutrients": nutrient_contributions
        }


async def create_recipe_calculator(
    usda_client: Optional[USDAClient] = None
) -> RecipeCalculator:
    """Factory function to create a RecipeCalculator with dependencies."""
    volume_converter = VolumeConverter(usda_client=usda_client)
    return RecipeCalculator(
        volume_converter=volume_converter,
        usda_client=usda_client
    )
