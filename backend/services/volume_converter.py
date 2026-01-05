"""
Volume-to-weight conversion service for recipe ingredients.

Converts volume measurements (cups, tablespoons, teaspoons) to grams
using a multi-source approach with confidence levels.
"""

from typing import Optional
from models.recipe import ConversionSource, ConversionResult
from data.conversion_data import (
    VOLUME_TO_GRAMS,
    INGREDIENT_ALIASES,
    PINCH_GRAMS,
    DASH_GRAMS,
    ML_PER_CUP,
    ML_PER_TBSP,
    ML_PER_TSP,
    ML_PER_FL_OZ,
)


class VolumeConverter:
    """
    Converts volume measurements to grams for recipe ingredients.

    Conversion priority:
    1. Direct weight (already in grams) → pass through
    2. Our curated conversion table → most reliable
    3. USDA foodPortions data → authoritative fallback
    4. LLM estimation → last resort, flagged for review
    """

    def __init__(self, usda_client=None, llm_client=None):
        self.usda_client = usda_client
        self.llm_client = llm_client

    def normalize_ingredient_name(self, name: str) -> str:
        """
        Normalize ingredient name to canonical form.

        Examples:
            "flour" → "all-purpose flour"
            "sugar" → "granulated sugar"
            "2 percent milk" → "2% milk"
        """
        normalized = name.lower().strip()

        # Remove common descriptors that don't affect weight
        descriptors_to_remove = [
            "softened", "melted", "room temperature", "cold", "warm",
            "sifted", "packed", "lightly packed", "firmly packed",
            "chopped", "diced", "minced", "sliced", "cubed",
            "fresh", "frozen", "thawed", "at room temperature",
        ]

        for desc in descriptors_to_remove:
            normalized = normalized.replace(f", {desc}", "")
            normalized = normalized.replace(f" {desc}", "")

        normalized = normalized.strip()

        # Check aliases first
        if normalized in INGREDIENT_ALIASES:
            return INGREDIENT_ALIASES[normalized]

        # Check if it's already a canonical name
        if normalized in VOLUME_TO_GRAMS:
            return normalized

        # Try partial matching
        for alias, canonical in INGREDIENT_ALIASES.items():
            if alias in normalized or normalized in alias:
                return canonical

        # Return original if no match
        return normalized

    def normalize_unit(self, unit: str) -> str:
        """Normalize unit string to standard form."""
        unit = unit.lower().strip()

        unit_map = {
            # Cups
            "cup": "cup",
            "cups": "cup",
            "c": "cup",
            "c.": "cup",

            # Tablespoons
            "tablespoon": "tbsp",
            "tablespoons": "tbsp",
            "tbsp": "tbsp",
            "tbsp.": "tbsp",
            "tbs": "tbsp",
            "tbs.": "tbsp",
            "tb": "tbsp",

            # Teaspoons
            "teaspoon": "tsp",
            "teaspoons": "tsp",
            "tsp": "tsp",
            "tsp.": "tsp",
            "t": "tsp",
            "t.": "tsp",

            # Fluid ounces
            "fluid ounce": "fl_oz",
            "fluid ounces": "fl_oz",
            "fl oz": "fl_oz",
            "fl. oz.": "fl_oz",
            "fl oz.": "fl_oz",

            # Weight units (pass-through)
            "gram": "g",
            "grams": "g",
            "g": "g",
            "kilogram": "kg",
            "kilograms": "kg",
            "kg": "kg",
            "ounce": "oz",
            "ounces": "oz",
            "oz": "oz",
            "oz.": "oz",
            "pound": "lb",
            "pounds": "lb",
            "lb": "lb",
            "lbs": "lb",
            "lb.": "lb",

            # Count units
            "whole": "whole",
            "large": "large",
            "medium": "medium",
            "small": "small",
            "each": "whole",
            "piece": "piece",
            "pieces": "piece",
            "slice": "slice",
            "slices": "slice",
            "clove": "clove",
            "cloves": "clove",
            "stick": "stick",
            "sticks": "stick",
            "packet": "packet",
            "packets": "packet",
            "pinch": "pinch",
            "dash": "dash",

            # Metric volume
            "milliliter": "ml",
            "milliliters": "ml",
            "ml": "ml",
            "liter": "l",
            "liters": "l",
            "l": "l",
        }

        return unit_map.get(unit, unit)

    def convert_to_grams(
        self,
        ingredient: str,
        quantity: float,
        unit: str
    ) -> ConversionResult:
        """
        Convert a volume measurement to grams.

        Args:
            ingredient: Ingredient name (will be normalized)
            quantity: Numeric amount
            unit: Unit of measurement

        Returns:
            ConversionResult with grams and metadata
        """
        normalized_name = self.normalize_ingredient_name(ingredient)
        normalized_unit = self.normalize_unit(unit)

        # 1. Already in grams - pass through
        if normalized_unit == "g":
            return ConversionResult(
                ingredient=normalized_name,
                original_quantity=quantity,
                original_unit=unit,
                grams=quantity,
                source=ConversionSource.DIRECT,
                confidence="high"
            )

        # 2. Convert other weight units to grams
        if normalized_unit == "kg":
            return ConversionResult(
                ingredient=normalized_name,
                original_quantity=quantity,
                original_unit=unit,
                grams=quantity * 1000,
                source=ConversionSource.DIRECT,
                confidence="high"
            )

        if normalized_unit == "oz":
            return ConversionResult(
                ingredient=normalized_name,
                original_quantity=quantity,
                original_unit=unit,
                grams=quantity * 28.35,
                source=ConversionSource.DIRECT,
                confidence="high"
            )

        if normalized_unit == "lb":
            return ConversionResult(
                ingredient=normalized_name,
                original_quantity=quantity,
                original_unit=unit,
                grams=quantity * 453.6,
                source=ConversionSource.DIRECT,
                confidence="high"
            )

        # 3. Handle pinch and dash
        if normalized_unit == "pinch":
            return ConversionResult(
                ingredient=normalized_name,
                original_quantity=quantity,
                original_unit=unit,
                grams=quantity * PINCH_GRAMS,
                source=ConversionSource.CONVERSION_TABLE,
                confidence="medium",
                note="Pinch estimated as ~1/16 tsp"
            )

        if normalized_unit == "dash":
            return ConversionResult(
                ingredient=normalized_name,
                original_quantity=quantity,
                original_unit=unit,
                grams=quantity * DASH_GRAMS,
                source=ConversionSource.CONVERSION_TABLE,
                confidence="medium",
                note="Dash estimated as ~1/8 tsp"
            )

        # 4. Check our conversion table
        if normalized_name in VOLUME_TO_GRAMS:
            conversion = VOLUME_TO_GRAMS[normalized_name]

            if normalized_unit in conversion:
                grams_per_unit = conversion[normalized_unit]
                return ConversionResult(
                    ingredient=normalized_name,
                    original_quantity=quantity,
                    original_unit=unit,
                    grams=quantity * grams_per_unit,
                    source=ConversionSource.CONVERSION_TABLE,
                    confidence="high"
                )

            # Handle count units (whole, large, medium, small)
            if normalized_unit in ("whole", "large", "medium", "small"):
                # Check for the specific size first
                if normalized_unit in conversion:
                    return ConversionResult(
                        ingredient=normalized_name,
                        original_quantity=quantity,
                        original_unit=unit,
                        grams=quantity * conversion[normalized_unit],
                        source=ConversionSource.CONVERSION_TABLE,
                        confidence="high"
                    )
                # Fall back to "whole" if available
                if "whole" in conversion:
                    return ConversionResult(
                        ingredient=normalized_name,
                        original_quantity=quantity,
                        original_unit=unit,
                        grams=quantity * conversion["whole"],
                        source=ConversionSource.CONVERSION_TABLE,
                        confidence="high"
                    )

            # Handle stick (for butter)
            if normalized_unit == "stick" and "stick" in conversion:
                return ConversionResult(
                    ingredient=normalized_name,
                    original_quantity=quantity,
                    original_unit=unit,
                    grams=quantity * conversion["stick"],
                    source=ConversionSource.CONVERSION_TABLE,
                    confidence="high"
                )

            # Handle packet (for yeast)
            if normalized_unit == "packet" and "packet" in conversion:
                return ConversionResult(
                    ingredient=normalized_name,
                    original_quantity=quantity,
                    original_unit=unit,
                    grams=quantity * conversion["packet"],
                    source=ConversionSource.CONVERSION_TABLE,
                    confidence="high"
                )

            # Try to convert using density if available
            if "density_g_per_ml" in conversion:
                ml = self._volume_to_ml(quantity, normalized_unit)
                if ml is not None:
                    grams = ml * conversion["density_g_per_ml"]
                    return ConversionResult(
                        ingredient=normalized_name,
                        original_quantity=quantity,
                        original_unit=unit,
                        grams=grams,
                        source=ConversionSource.CONVERSION_TABLE,
                        confidence="high",
                        note="Converted using density"
                    )

        # 5. Fallback for ALL volume units - assume water-like density
        # This handles ingredients from USDA that aren't in our conversion table
        if normalized_unit in ("ml", "l", "fl_oz", "cup", "tbsp", "tsp"):
            ml = self._volume_to_ml(quantity, normalized_unit)
            if ml is not None:
                # Assume density close to water (1.0 g/ml) for unknown ingredients
                # Most food ingredients are 0.5-1.5 g/ml
                grams = ml * 1.0
                return ConversionResult(
                    ingredient=normalized_name,
                    original_quantity=quantity,
                    original_unit=unit,
                    grams=grams,
                    source=ConversionSource.CONVERSION_TABLE,
                    confidence="medium",
                    note="Estimated using water density (1.0 g/ml). Adjust if needed."
                )

        # 6. Fallback for count units - use reasonable defaults
        # These are rough estimates for unknown ingredients
        count_defaults = {
            "whole": 50.0,    # ~medium egg or small fruit
            "large": 60.0,    # ~large egg
            "medium": 50.0,   # ~medium egg
            "small": 40.0,    # ~small egg
            "piece": 30.0,    # generic piece
            "slice": 30.0,    # generic slice
            "clove": 3.0,     # garlic clove
            "stick": 113.0,   # butter stick
            "packet": 7.0,    # yeast packet
        }

        if normalized_unit in count_defaults:
            default_grams = count_defaults[normalized_unit]
            return ConversionResult(
                ingredient=normalized_name,
                original_quantity=quantity,
                original_unit=unit,
                grams=quantity * default_grams,
                source=ConversionSource.LLM_ESTIMATE,
                confidence="low",
                note=f"Estimated {default_grams}g per {normalized_unit}. Please verify and adjust."
            )

        # 7. Try USDA portions (async call would need to be handled by caller)
        # For now, skip this step in the sync method

        # 8. Try LLM estimation
        if self.llm_client:
            llm_result = self._try_llm_estimation(ingredient, quantity, unit)
            if llm_result:
                return llm_result

        # 9. Unable to convert - flag for manual entry
        return ConversionResult(
            ingredient=normalized_name,
            original_quantity=quantity,
            original_unit=unit,
            grams=0,
            source=ConversionSource.LLM_ESTIMATE,
            confidence="low",
            note=f"Could not convert {quantity} {unit} of {ingredient}. Please enter weight manually."
        )

    def _volume_to_ml(self, quantity: float, unit: str) -> Optional[float]:
        """Convert volume unit to milliliters."""
        unit = unit.lower()

        if unit == "cup":
            return quantity * ML_PER_CUP
        elif unit == "tbsp":
            return quantity * ML_PER_TBSP
        elif unit == "tsp":
            return quantity * ML_PER_TSP
        elif unit == "fl_oz":
            return quantity * ML_PER_FL_OZ
        elif unit == "ml":
            return quantity
        elif unit == "l":
            return quantity * 1000

        return None

    def _try_llm_estimation(
        self,
        ingredient: str,
        quantity: float,
        unit: str
    ) -> Optional[ConversionResult]:
        """Use LLM to estimate weight for unknown ingredients."""
        if not self.llm_client:
            return None

        prompt = f"""
Estimate the weight in grams for this ingredient measurement:

Ingredient: {ingredient}
Amount: {quantity} {unit}

Based on your knowledge of common ingredient densities, provide your best estimate.

Respond with JSON only:
{{
    "grams": <number>,
    "confidence": "high" | "medium" | "low",
    "reasoning": "<brief explanation>"
}}
"""

        try:
            import json

            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            result = json.loads(response.choices[0].message.content)

            return ConversionResult(
                ingredient=ingredient,
                original_quantity=quantity,
                original_unit=unit,
                grams=result["grams"],
                source=ConversionSource.LLM_ESTIMATE,
                confidence=result.get("confidence", "low"),
                note=f"LLM estimate: {result.get('reasoning', 'No reasoning provided')}"
            )

        except Exception:
            return None

    async def convert_to_grams_async(
        self,
        ingredient: str,
        quantity: float,
        unit: str
    ) -> ConversionResult:
        """
        Async version of convert_to_grams that can use USDA data.

        Args:
            ingredient: Ingredient name (will be normalized)
            quantity: Numeric amount
            unit: Unit of measurement

        Returns:
            ConversionResult with grams and metadata
        """
        # First try the sync conversion
        result = self.convert_to_grams(ingredient, quantity, unit)

        # If we got a good result, return it
        if result.confidence == "high":
            return result

        # Try USDA if we have a client and the sync method didn't work well
        if self.usda_client and result.confidence == "low":
            usda_result = await self._try_usda_conversion(
                self.normalize_ingredient_name(ingredient),
                quantity,
                self.normalize_unit(unit)
            )
            if usda_result:
                return usda_result

        return result

    async def _try_usda_conversion(
        self,
        ingredient: str,
        quantity: float,
        unit: str
    ) -> Optional[ConversionResult]:
        """Attempt conversion using USDA portion data."""
        try:
            # Search for the ingredient
            results = await self.usda_client.search(ingredient, page_size=5)
            if not results:
                return None

            # Get the first result's full data
            fdc_id = results[0]["fdc_id"]
            food_data = await self.usda_client.get_food(fdc_id)

            if not food_data:
                return None

            # Look for matching portion
            for portion in food_data.get("foodPortions", []):
                portion_unit = portion.get("measureUnit", {}).get("name", "").lower()

                if self.normalize_unit(portion_unit) == unit:
                    gram_weight = portion.get("gramWeight", 0)
                    portion_amount = portion.get("amount", 1)

                    grams = (quantity / portion_amount) * gram_weight

                    return ConversionResult(
                        ingredient=ingredient,
                        original_quantity=quantity,
                        original_unit=unit,
                        grams=grams,
                        source=ConversionSource.USDA_PORTION,
                        confidence="high",
                        note=f"From USDA: {portion.get('modifier', '')}"
                    )

            return None

        except Exception:
            return None


def get_supported_ingredients() -> list[dict]:
    """
    Get list of all ingredients with volume conversion data.

    Returns:
        List of ingredient info dicts
    """
    ingredients = []
    for name, data in VOLUME_TO_GRAMS.items():
        if "alias_for" not in data:
            ingredients.append({
                "name": name,
                "has_cup": "cup" in data,
                "has_tbsp": "tbsp" in data,
                "has_tsp": "tsp" in data,
                "has_whole": "whole" in data,
                "has_stick": "stick" in data,
                "notes": data.get("notes")
            })

    return sorted(ingredients, key=lambda x: x["name"])
