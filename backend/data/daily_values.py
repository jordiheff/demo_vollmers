"""
FDA Daily Reference Values (DRVs) based on a 2,000 calorie diet.
Source: 21 CFR 101.9 and FDA Daily Value guidance (2020 update)

References:
- 21 CFR § 101.9: https://www.law.cornell.edu/cfr/text/21/101.9
- FDA Food Labeling Guide Appendix H
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

# FDA Daily Values for nutrition labeling
DAILY_VALUES = {
    # Macronutrients
    "total_fat_g": 78,          # grams
    "saturated_fat_g": 20,      # grams
    # trans_fat has no DV
    "cholesterol_mg": 300,      # milligrams
    "sodium_mg": 2300,          # milligrams
    "total_carbohydrate_g": 275,  # grams
    "dietary_fiber_g": 28,      # grams
    # total_sugars has no DV
    "added_sugars_g": 50,       # grams
    "protein_g": 50,            # grams (optional display)

    # Vitamins and minerals (required on 2020 label)
    "vitamin_d_mcg": 20,        # micrograms
    "calcium_mg": 1300,         # milligrams
    "iron_mg": 18,              # milligrams
    "potassium_mg": 4700,       # milligrams

    # Additional vitamins (optional display)
    "vitamin_a_mcg": 900,       # micrograms RAE
    "vitamin_c_mg": 90,         # milligrams
    "vitamin_e_mg": 15,         # milligrams alpha-tocopherol
    "vitamin_k_mcg": 120,       # micrograms
    "thiamin_mg": 1.2,          # milligrams (B1)
    "riboflavin_mg": 1.3,       # milligrams (B2)
    "niacin_mg": 16,            # milligrams (B3)
    "vitamin_b6_mg": 1.7,       # milligrams
    "folate_mcg": 400,          # micrograms DFE
    "vitamin_b12_mcg": 2.4,     # micrograms

    # Additional minerals (optional display)
    "phosphorus_mg": 1250,      # milligrams
    "magnesium_mg": 420,        # milligrams
    "zinc_mg": 11,              # milligrams
    "copper_mg": 0.9,           # milligrams
    "manganese_mg": 2.3,        # milligrams
    "selenium_mcg": 55,         # micrograms
    "chromium_mcg": 35,         # micrograms
    "molybdenum_mcg": 45,       # micrograms
    "chloride_mg": 2300,        # milligrams
    "biotin_mcg": 30,           # micrograms
    "pantothenic_acid_mg": 5,   # milligrams
    "choline_mg": 550,          # milligrams
}

# Nutrients that do not have a %DV
NO_DV_NUTRIENTS = {"trans_fat_g", "total_sugars_g"}

# Vitamins and minerals that use tiered %DV rounding
VITAMIN_MINERAL_NUTRIENTS = {
    "vitamin_d_mcg", "calcium_mg", "iron_mg", "potassium_mg",
    "vitamin_a_mcg", "vitamin_c_mg", "vitamin_e_mg", "vitamin_k_mcg",
    "thiamin_mg", "riboflavin_mg", "niacin_mg", "vitamin_b6_mg",
    "folate_mcg", "vitamin_b12_mcg", "phosphorus_mg", "magnesium_mg",
    "zinc_mg", "copper_mg", "manganese_mg", "selenium_mcg",
    "chromium_mcg", "molybdenum_mcg", "chloride_mg", "biotin_mcg",
    "pantothenic_acid_mg", "choline_mg"
}


def _fda_round_dv(percent: float, increment: int) -> int:
    """
    Round %DV to the nearest increment using FDA 'round half up' rule.

    FDA guidance specifies "halfway rounds up" behavior, not Python's
    default banker's rounding (round half to even).

    Args:
        percent: The percent DV value
        increment: The rounding increment (1, 2, 5, or 10)

    Returns:
        Percent DV rounded to nearest increment using round-half-up
    """
    d_value = Decimal(str(percent))
    d_increment = Decimal(str(increment))

    # Divide by increment, round to nearest integer (half up), multiply back
    rounded = int((d_value / d_increment).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * d_increment)

    return rounded


def get_percent_dv(nutrient_key: str, amount: Optional[float]) -> Optional[int]:
    """
    Calculate percent Daily Value for a nutrient amount.

    Uses FDA rounding rules from 21 CFR 101.9(c)(8)(iii) and Appendix H:
    - For macronutrients: round to nearest 1% (half up)
    - For vitamins/minerals:
        - ≤10% DV: round to nearest 2%
        - >10% to ≤50% DV: round to nearest 5%
        - >50% DV: round to nearest 10%

    Args:
        nutrient_key: Key matching DAILY_VALUES (e.g., "total_fat_g")
        amount: Amount of the nutrient

    Returns:
        Percent DV rounded per FDA rules, or None if no DV exists
    """
    if amount is None:
        return None

    if nutrient_key in NO_DV_NUTRIENTS:
        return None

    dv = DAILY_VALUES.get(nutrient_key)
    if dv is None:
        return None

    percent = (amount / dv) * 100

    # Vitamins and minerals use tiered rounding per 21 CFR 101.9(c)(8)(iii)
    if nutrient_key in VITAMIN_MINERAL_NUTRIENTS:
        if percent <= 10:
            return _fda_round_dv(percent, 2)
        elif percent <= 50:
            return _fda_round_dv(percent, 5)
        else:
            return _fda_round_dv(percent, 10)

    # Macronutrients round to nearest 1% (half up)
    return _fda_round_dv(percent, 1)
