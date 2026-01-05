"""
USDA FoodData Central nutrient ID mappings.
"""

# Map of USDA nutrient IDs to our schema fields
USDA_NUTRIENT_MAP = {
    # Core macronutrients
    1008: ("calories", "kcal"),              # Energy
    1003: ("protein_g", "g"),                # Protein
    1004: ("total_fat_g", "g"),              # Total lipid (fat)
    1005: ("total_carbohydrate_g", "g"),     # Carbohydrate, by difference

    # Fats breakdown
    1258: ("saturated_fat_g", "g"),          # Fatty acids, total saturated
    1257: ("trans_fat_g", "g"),              # Fatty acids, total trans
    1292: ("monounsaturated_fat_g", "g"),    # Fatty acids, total monounsaturated
    1293: ("polyunsaturated_fat_g", "g"),    # Fatty acids, total polyunsaturated

    # Other core nutrients
    1253: ("cholesterol_mg", "mg"),          # Cholesterol
    1093: ("sodium_mg", "mg"),               # Sodium, Na
    1079: ("dietary_fiber_g", "g"),          # Fiber, total dietary
    1082: ("soluble_fiber_g", "g"),          # Fiber, soluble
    1084: ("insoluble_fiber_g", "g"),        # Fiber, insoluble

    # Sugars
    2000: ("total_sugars_g", "g"),           # Sugars, total including NLEA
    1235: ("added_sugars_g", "g"),           # Sugars, added

    # Minerals (FDA required)
    1087: ("calcium_mg", "mg"),              # Calcium, Ca
    1089: ("iron_mg", "mg"),                 # Iron, Fe
    1092: ("potassium_mg", "mg"),            # Potassium, K

    # Vitamins (FDA required)
    1114: ("vitamin_d_mcg", "mcg"),          # Vitamin D (D2 + D3)

    # Additional vitamins (optional display)
    1106: ("vitamin_a_iu", "IU"),            # Vitamin A, IU
    1162: ("vitamin_c_mg", "mg"),            # Vitamin C, total ascorbic acid
    1109: ("vitamin_e_mg", "mg"),            # Vitamin E (alpha-tocopherol)
    1183: ("vitamin_k_mcg", "mcg"),          # Vitamin K (phylloquinone)
    1165: ("thiamin_mg", "mg"),              # Thiamin (B1)
    1166: ("riboflavin_mg", "mg"),           # Riboflavin (B2)
    1167: ("niacin_mg", "mg"),               # Niacin (B3)
    1175: ("vitamin_b6_mg", "mg"),           # Vitamin B-6
    1178: ("vitamin_b12_mcg", "mcg"),        # Vitamin B-12
    1177: ("folate_mcg", "mcg"),             # Folate, total

    # Additional minerals (optional display)
    1091: ("phosphorus_mg", "mg"),           # Phosphorus, P
    1090: ("magnesium_mg", "mg"),            # Magnesium, Mg
    1095: ("zinc_mg", "mg"),                 # Zinc, Zn
    1098: ("copper_mg", "mg"),               # Copper, Cu
    1103: ("selenium_mcg", "mcg"),           # Selenium, Se
}

# Nutrients required for FDA labels (2020 format)
FDA_REQUIRED_NUTRIENTS = [
    1008,  # Calories
    1004,  # Total Fat
    1258,  # Saturated Fat
    1257,  # Trans Fat
    1253,  # Cholesterol
    1093,  # Sodium
    1005,  # Total Carbohydrate
    1079,  # Dietary Fiber
    2000,  # Total Sugars
    1235,  # Added Sugars
    1003,  # Protein
    1114,  # Vitamin D
    1087,  # Calcium
    1089,  # Iron
    1092,  # Potassium
]
