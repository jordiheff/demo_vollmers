"""
Nutrition calculation service for per-serving values and %DV.
Implements FDA 21 CFR 101.9 rounding rules.

References:
- 21 CFR § 101.9: https://www.law.cornell.edu/cfr/text/21/101.9
- FDA Food Labeling Guide Appendix H
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from models.nutrition import NutritionPer100g, ServingConfig, NutritionPerServing
from data.daily_values import get_percent_dv


def _fda_round(value: float, increment: float) -> float:
    """
    Round a value to the nearest increment using FDA 'round half up' rule.

    FDA guidance specifies "halfway rounds up" behavior, not Python's
    default banker's rounding (round half to even).

    Args:
        value: The value to round
        increment: The rounding increment (e.g., 5 for nearest 5, 0.5 for nearest 0.5)

    Returns:
        Value rounded to nearest increment using round-half-up
    """
    if increment == 0:
        return value

    # Convert to Decimal for precise rounding
    d_value = Decimal(str(value))
    d_increment = Decimal(str(increment))

    # Divide by increment, round to nearest integer (half up), multiply back
    rounded = (d_value / d_increment).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * d_increment

    return float(rounded)


class NutritionCalculator:
    """Calculate per-serving nutrition values with FDA rounding."""

    @staticmethod
    def calculate_per_serving(
        nutrition: NutritionPer100g,
        serving_config: ServingConfig
    ) -> NutritionPerServing:
        """
        Calculate per-serving values from per-100g data.

        Args:
            nutrition: Nutrition values per 100g
            serving_config: Serving size configuration

        Returns:
            NutritionPerServing with calculated values and %DV
        """
        factor = serving_config.serving_size_g / 100.0

        # Calculate raw per-serving values
        calories = NutritionCalculator._scale(nutrition.calories, factor)
        total_fat = NutritionCalculator._scale(nutrition.total_fat_g, factor)
        saturated_fat = NutritionCalculator._scale(nutrition.saturated_fat_g, factor)
        trans_fat = NutritionCalculator._scale(nutrition.trans_fat_g, factor)
        cholesterol = NutritionCalculator._scale(nutrition.cholesterol_mg, factor)
        sodium = NutritionCalculator._scale(nutrition.sodium_mg, factor)
        total_carb = NutritionCalculator._scale(nutrition.total_carbohydrate_g, factor)
        fiber = NutritionCalculator._scale(nutrition.dietary_fiber_g, factor)
        total_sugars = NutritionCalculator._scale(nutrition.total_sugars_g, factor)
        added_sugars = NutritionCalculator._scale(nutrition.added_sugars_g, factor)
        protein = NutritionCalculator._scale(nutrition.protein_g, factor)
        vitamin_d = NutritionCalculator._scale(nutrition.vitamin_d_mcg, factor)
        calcium = NutritionCalculator._scale(nutrition.calcium_mg, factor)
        iron = NutritionCalculator._scale(nutrition.iron_mg, factor)
        potassium = NutritionCalculator._scale(nutrition.potassium_mg, factor)

        # Apply FDA rounding rules
        calories_rounded = NutritionCalculator._round_calories(calories)
        total_fat_rounded = NutritionCalculator._round_fat(total_fat)
        saturated_fat_rounded = NutritionCalculator._round_fat(saturated_fat)
        trans_fat_rounded = NutritionCalculator._round_fat(trans_fat)
        cholesterol_rounded = NutritionCalculator._round_cholesterol(cholesterol)
        sodium_rounded = NutritionCalculator._round_sodium_potassium(sodium)
        total_carb_rounded = NutritionCalculator._round_carb_protein(total_carb)
        fiber_rounded = NutritionCalculator._round_carb_protein(fiber)
        total_sugars_rounded = NutritionCalculator._round_carb_protein(total_sugars)
        added_sugars_rounded = NutritionCalculator._round_carb_protein(added_sugars)
        protein_rounded = NutritionCalculator._round_carb_protein(protein)
        potassium_rounded = NutritionCalculator._round_sodium_potassium(potassium)

        # Calculate %DV (using unrounded values for accuracy)
        # Convert serving_config to dict for Pydantic v2 compatibility
        serving_config_dict = serving_config.model_dump() if hasattr(serving_config, 'model_dump') else serving_config.dict()

        return NutritionPerServing(
            serving_config=serving_config_dict,
            calories=calories_rounded,
            total_fat_g=total_fat_rounded,
            total_fat_dv=get_percent_dv("total_fat_g", total_fat),
            saturated_fat_g=saturated_fat_rounded,
            saturated_fat_dv=get_percent_dv("saturated_fat_g", saturated_fat),
            trans_fat_g=trans_fat_rounded,
            cholesterol_mg=cholesterol_rounded,
            cholesterol_dv=get_percent_dv("cholesterol_mg", cholesterol),
            sodium_mg=sodium_rounded,
            sodium_dv=get_percent_dv("sodium_mg", sodium),
            total_carbohydrate_g=total_carb_rounded,
            total_carbohydrate_dv=get_percent_dv("total_carbohydrate_g", total_carb),
            dietary_fiber_g=fiber_rounded,
            dietary_fiber_dv=get_percent_dv("dietary_fiber_g", fiber),
            total_sugars_g=total_sugars_rounded,
            added_sugars_g=added_sugars_rounded,
            added_sugars_dv=get_percent_dv("added_sugars_g", added_sugars),
            protein_g=protein_rounded,
            vitamin_d_mcg=vitamin_d,  # Vitamins use different rounding
            vitamin_d_dv=get_percent_dv("vitamin_d_mcg", vitamin_d),
            calcium_mg=calcium,
            calcium_dv=get_percent_dv("calcium_mg", calcium),
            iron_mg=iron,
            iron_dv=get_percent_dv("iron_mg", iron),
            potassium_mg=potassium_rounded,
            potassium_dv=get_percent_dv("potassium_mg", potassium),
        )

    @staticmethod
    def _scale(value: Optional[float], factor: float) -> Optional[float]:
        """Scale a value by a factor, preserving None."""
        if value is None:
            return None
        return value * factor

    @staticmethod
    def _round_calories(value: Optional[float]) -> Optional[float]:
        """
        Round calories per FDA rules (21 CFR 101.9).

        <5 cal: 0
        ≤50 cal: nearest 5
        >50 cal: nearest 10

        Source: FDA Food Labeling Guide Appendix H
        """
        if value is None:
            return None

        if value < 5:
            return 0
        elif value <= 50:
            return _fda_round(value, 5)
        else:
            return _fda_round(value, 10)

    @staticmethod
    def _round_fat(value: Optional[float]) -> Optional[float]:
        """
        Round fat values per FDA rules (21 CFR 101.9(c)(2)).

        <0.5g: 0
        0.5g to <5g: nearest 0.5g
        ≥5g: nearest 1g

        Source: FDA Food Labeling Guide Appendix H
        """
        if value is None:
            return None

        if value < 0.5:
            return 0
        elif value < 5:
            return _fda_round(value, 0.5)
        else:
            return _fda_round(value, 1)

    @staticmethod
    def _round_cholesterol(value: Optional[float]) -> Optional[float]:
        """
        Round cholesterol per FDA rules (21 CFR 101.9(c)(3)).

        <2mg: 0
        2-5mg: "less than 5mg" (we return 2 as marker)
        >5mg: nearest 5mg

        Source: FDA Food Labeling Guide Appendix H
        """
        if value is None:
            return None

        if value < 2:
            return 0
        elif value <= 5:
            return 2  # Represents "less than 5mg"
        else:
            return _fda_round(value, 5)

    @staticmethod
    def _round_sodium_potassium(value: Optional[float]) -> Optional[float]:
        """
        Round sodium/potassium per FDA rules (21 CFR 101.9(c)(4)).

        <5mg: 0
        5-140mg: nearest 5mg
        >140mg: nearest 10mg

        Source: FDA Food Labeling Guide Appendix H
        """
        if value is None:
            return None

        if value < 5:
            return 0
        elif value <= 140:
            return _fda_round(value, 5)
        else:
            return _fda_round(value, 10)

    @staticmethod
    def _round_carb_protein(value: Optional[float]) -> Optional[float]:
        """
        Round carbs, fiber, sugars, protein per FDA rules (21 CFR 101.9(c)(6-7)).

        <0.5g: 0
        0.5g to <1g: "less than 1g" (we return 0.5 as marker)
        ≥1g: nearest 1g

        Source: FDA Food Labeling Guide Appendix H
        """
        if value is None:
            return None

        if value < 0.5:
            return 0
        elif value < 1:
            return 0.5  # Represents "less than 1g"
        else:
            return _fda_round(value, 1)

    @staticmethod
    def _round_fluoride(value: Optional[float]) -> Optional[float]:
        """
        Round fluoride per FDA rules (21 CFR 101.9(c)(5)).

        <0.1mg: 0
        ≤0.8mg: nearest 0.1mg
        >0.8mg: nearest 0.2mg

        Source: FDA Food Labeling Guide Appendix H
        """
        if value is None:
            return None

        if value < 0.1:
            return 0
        elif value <= 0.8:
            return _fda_round(value, 0.1)
        else:
            return _fda_round(value, 0.2)

    @staticmethod
    def round_serving_size_metric(value: float) -> float:
        """
        Round serving size metric (g or mL) per FDA rules (21 CFR 101.9(b)(5)).

        ≥5g: nearest whole number
        2 to <5g: nearest 0.5g
        <2g: nearest 0.1g

        Source: 21 CFR 101.9(b)(5)(ii)-(iii)
        """
        if value >= 5:
            return _fda_round(value, 1)
        elif value >= 2:
            return _fda_round(value, 0.5)
        else:
            return _fda_round(value, 0.1)

    @staticmethod
    def round_servings_per_container(value: float) -> tuple[float, bool]:
        """
        Round servings per container per FDA rules (21 CFR 101.9(b)(8)).

        Returns tuple of (rounded_value, use_about_prefix).

        >5 servings: nearest whole number, no prefix
        2-5 servings: nearest 0.5, use "about" prefix
        <2 servings: nearest whole number (1), no prefix

        Source: 21 CFR 101.9(b)(8)(i)-(v) and FDA Serving Size Guidance
        """
        if value > 5:
            return (_fda_round(value, 1), False)
        elif value >= 2:
            return (_fda_round(value, 0.5), True)  # Use "about" prefix
        else:
            return (_fda_round(value, 1), False)

    @staticmethod
    def format_servings_per_container(value: float) -> str:
        """
        Format servings per container for label display.

        Applies FDA rounding and adds "about" prefix when required.

        Args:
            value: Raw servings per container

        Returns:
            Formatted string (e.g., "about 3.5 servings", "10 servings")
        """
        rounded, use_about = NutritionCalculator.round_servings_per_container(value)

        # Format the number
        if rounded == int(rounded):
            num_str = str(int(rounded))
        else:
            num_str = f"{rounded:.1f}"

        # Add prefix and suffix
        prefix = "about " if use_about else ""
        suffix = " serving" if rounded == 1 else " servings"

        return f"{prefix}{num_str}{suffix}"

    @staticmethod
    def format_value_for_label(
        field: str,
        value: Optional[float]
    ) -> str:
        """
        Format a nutrition value for display on the label.

        Args:
            field: Field name (e.g., "calories", "cholesterol_mg")
            value: Rounded value

        Returns:
            Formatted string for label display
        """
        if value is None:
            return "—"

        # Handle "less than" cases
        if field == "cholesterol_mg" and value == 2:
            return "Less than 5mg"

        if field in ["total_carbohydrate_g", "dietary_fiber_g",
                     "total_sugars_g", "added_sugars_g", "protein_g"]:
            if value == 0.5:
                return "Less than 1g"

        # Regular formatting
        if field == "calories":
            return str(int(value))

        # Determine unit
        if field.endswith("_mg"):
            unit = "mg"
        elif field.endswith("_mcg"):
            unit = "mcg"
        elif field.endswith("_g"):
            unit = "g"
        else:
            unit = ""

        # Format number
        if value == int(value):
            return f"{int(value)}{unit}"
        else:
            return f"{value:.1f}{unit}"
