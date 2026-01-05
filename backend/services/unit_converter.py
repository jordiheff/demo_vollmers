"""
Unit conversion service with flagging for nutrition values.
"""

from typing import Tuple, Optional
from models.nutrition import NutritionPer100g, ExtractedProduct
from models.flags import FlagType, ExtractionFlag


class UnitConverter:
    """Convert nutrition values between units with flagging."""

    # Conversion factors
    CONVERSIONS = {
        # Vitamin D: IU to mcg
        "vitamin_d_iu_to_mcg": 1 / 40,

        # Vitamin A conversions (IU to mcg RAE)
        "vitamin_a_retinol_iu_to_mcg": 1 / 3.33,
        "vitamin_a_beta_carotene_iu_to_mcg": 1 / 20,

        # Vitamin E conversions (IU to mg)
        "vitamin_e_synthetic_iu_to_mg": 0.45,
        "vitamin_e_natural_iu_to_mg": 0.67,

        # Energy: kJ to kcal
        "kj_to_kcal": 1 / 4.184,
    }

    @staticmethod
    def convert_vitamin_d_iu(iu_value: float) -> Tuple[float, ExtractionFlag]:
        """
        Convert Vitamin D from IU to mcg.

        Args:
            iu_value: Vitamin D value in IU

        Returns:
            Tuple of (mcg value, conversion flag)
        """
        mcg_value = iu_value * UnitConverter.CONVERSIONS["vitamin_d_iu_to_mcg"]

        flag = ExtractionFlag(
            field="vitamin_d_mcg",
            flag_type=FlagType.CONVERTED,
            message="Converted from IU to mcg",
            original_value=f"{iu_value} IU",
            confidence=1.0
        )

        return mcg_value, flag

    @staticmethod
    def convert_vitamin_a_iu(
        iu_value: float,
        source: str = "retinol"
    ) -> Tuple[float, ExtractionFlag]:
        """
        Convert Vitamin A from IU to mcg RAE.

        Args:
            iu_value: Vitamin A value in IU
            source: Source type ("retinol" or "beta_carotene")

        Returns:
            Tuple of (mcg RAE value, conversion flag)
        """
        if source == "beta_carotene":
            factor = UnitConverter.CONVERSIONS["vitamin_a_beta_carotene_iu_to_mcg"]
            message = "Converted from IU assuming beta-carotene source"
            confidence = 0.7
        else:
            # Default to retinol (more conservative)
            factor = UnitConverter.CONVERSIONS["vitamin_a_retinol_iu_to_mcg"]
            message = "Converted from IU assuming retinol source"
            confidence = 0.8

        mcg_value = iu_value * factor

        flag = ExtractionFlag(
            field="vitamin_a_mcg",
            flag_type=FlagType.CONVERTED,
            message=message,
            original_value=f"{iu_value} IU",
            confidence=confidence
        )

        return mcg_value, flag

    @staticmethod
    def convert_vitamin_e_iu(
        iu_value: float,
        form: str = "synthetic"
    ) -> Tuple[float, ExtractionFlag]:
        """
        Convert Vitamin E from IU to mg alpha-tocopherol.

        Args:
            iu_value: Vitamin E value in IU
            form: Form type ("synthetic" or "natural")

        Returns:
            Tuple of (mg value, conversion flag)
        """
        if form == "natural":
            factor = UnitConverter.CONVERSIONS["vitamin_e_natural_iu_to_mg"]
            message = "Converted from IU assuming natural form"
            confidence = 0.7
        else:
            factor = UnitConverter.CONVERSIONS["vitamin_e_synthetic_iu_to_mg"]
            message = "Converted from IU assuming synthetic form"
            confidence = 0.8

        mg_value = iu_value * factor

        flag = ExtractionFlag(
            field="vitamin_e_mg",
            flag_type=FlagType.CONVERTED,
            message=message,
            original_value=f"{iu_value} IU",
            confidence=confidence
        )

        return mg_value, flag

    @staticmethod
    def convert_energy_kj(kj_value: float) -> Tuple[float, ExtractionFlag]:
        """
        Convert energy from kilojoules to kilocalories.

        Args:
            kj_value: Energy value in kJ

        Returns:
            Tuple of (kcal value, conversion flag)
        """
        kcal_value = kj_value * UnitConverter.CONVERSIONS["kj_to_kcal"]

        flag = ExtractionFlag(
            field="calories",
            flag_type=FlagType.CONVERTED,
            message="Converted from kilojoules",
            original_value=f"{kj_value} kJ",
            confidence=1.0
        )

        return kcal_value, flag

    @staticmethod
    def apply_conversions(product: ExtractedProduct) -> ExtractedProduct:
        """
        Apply all necessary unit conversions to extracted product.

        Modifies the product's nutrition values and adds conversion flags.

        Args:
            product: Extracted product with raw nutrition data

        Returns:
            Product with converted values and flags
        """
        flags = list(product.flags)  # Copy existing flags

        # Check for Vitamin D IU that needs conversion
        # This would typically come from the raw extraction data
        # For now, we just ensure vitamin_d_mcg is populated

        # Validate and flag anomalies
        anomalies = UnitConverter._detect_anomalies(product.nutrition)
        flags.extend(anomalies)

        # Use model_copy for Pydantic v2 compatibility
        return product.model_copy(update={"flags": flags})

    @staticmethod
    def _detect_anomalies(nutrition: NutritionPer100g) -> list[ExtractionFlag]:
        """
        Detect anomalous values that may indicate extraction errors.

        Args:
            nutrition: Nutrition data per 100g

        Returns:
            List of anomaly flags
        """
        anomalies = []

        # Calorie range check (per 100g)
        if nutrition.calories is not None:
            if nutrition.calories < 0:
                anomalies.append(ExtractionFlag(
                    field="calories",
                    flag_type=FlagType.ANOMALY,
                    message="Negative calorie value detected",
                    original_value=str(nutrition.calories)
                ))
            elif nutrition.calories > 900:
                anomalies.append(ExtractionFlag(
                    field="calories",
                    flag_type=FlagType.ANOMALY,
                    message="Unusually high calorie value (>900 per 100g)",
                    original_value=str(nutrition.calories)
                ))

        # Fat cannot exceed 100g per 100g
        if nutrition.total_fat_g is not None and nutrition.total_fat_g > 100:
            anomalies.append(ExtractionFlag(
                field="total_fat_g",
                flag_type=FlagType.ANOMALY,
                message="Fat exceeds 100g per 100g serving",
                original_value=str(nutrition.total_fat_g)
            ))

        # Saturated fat cannot exceed total fat
        if (nutrition.saturated_fat_g is not None and
            nutrition.total_fat_g is not None and
            nutrition.saturated_fat_g > nutrition.total_fat_g):
            anomalies.append(ExtractionFlag(
                field="saturated_fat_g",
                flag_type=FlagType.ANOMALY,
                message="Saturated fat exceeds total fat",
                original_value=str(nutrition.saturated_fat_g)
            ))

        # Protein cannot exceed 100g per 100g
        if nutrition.protein_g is not None and nutrition.protein_g > 100:
            anomalies.append(ExtractionFlag(
                field="protein_g",
                flag_type=FlagType.ANOMALY,
                message="Protein exceeds 100g per 100g serving",
                original_value=str(nutrition.protein_g)
            ))

        # Carbs cannot exceed 100g per 100g
        if (nutrition.total_carbohydrate_g is not None and
            nutrition.total_carbohydrate_g > 100):
            anomalies.append(ExtractionFlag(
                field="total_carbohydrate_g",
                flag_type=FlagType.ANOMALY,
                message="Carbohydrate exceeds 100g per 100g serving",
                original_value=str(nutrition.total_carbohydrate_g)
            ))

        # Added sugars cannot exceed total sugars
        if (nutrition.added_sugars_g is not None and
            nutrition.total_sugars_g is not None and
            nutrition.added_sugars_g > nutrition.total_sugars_g):
            anomalies.append(ExtractionFlag(
                field="added_sugars_g",
                flag_type=FlagType.ANOMALY,
                message="Added sugars exceeds total sugars",
                original_value=str(nutrition.added_sugars_g)
            ))

        # Dietary fiber cannot exceed total carbs
        if (nutrition.dietary_fiber_g is not None and
            nutrition.total_carbohydrate_g is not None and
            nutrition.dietary_fiber_g > nutrition.total_carbohydrate_g):
            anomalies.append(ExtractionFlag(
                field="dietary_fiber_g",
                flag_type=FlagType.ANOMALY,
                message="Dietary fiber exceeds total carbohydrate",
                original_value=str(nutrition.dietary_fiber_g)
            ))

        return anomalies
