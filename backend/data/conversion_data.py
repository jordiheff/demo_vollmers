"""
Volume-to-weight conversion factors for common baking ingredients.

Sources:
- USDA FoodData Central
- King Arthur Flour weight chart
- Serious Eats ingredient weight database

All values are in grams.
"""

VOLUME_TO_GRAMS: dict[str, dict] = {
    # =========================================================================
    # FLOURS & STARCHES
    # =========================================================================
    "all-purpose flour": {
        "cup": 125,
        "tbsp": 7.8,
        "tsp": 2.6,
        "notes": "Spooned and leveled, not scooped"
    },
    "bread flour": {
        "cup": 127,
        "tbsp": 7.9,
        "tsp": 2.6,
    },
    "cake flour": {
        "cup": 114,
        "tbsp": 7.1,
        "tsp": 2.4,
    },
    "whole wheat flour": {
        "cup": 120,
        "tbsp": 7.5,
        "tsp": 2.5,
    },
    "pastry flour": {
        "cup": 106,
        "tbsp": 6.6,
        "tsp": 2.2,
    },
    "almond flour": {
        "cup": 96,
        "tbsp": 6.0,
        "tsp": 2.0,
    },
    "coconut flour": {
        "cup": 112,
        "tbsp": 7.0,
        "tsp": 2.3,
    },
    "cornstarch": {
        "cup": 128,
        "tbsp": 8.0,
        "tsp": 2.7,
    },
    "tapioca starch": {
        "cup": 120,
        "tbsp": 7.5,
        "tsp": 2.5,
    },
    "potato starch": {
        "cup": 160,
        "tbsp": 10.0,
        "tsp": 3.3,
    },
    "rice flour": {
        "cup": 158,
        "tbsp": 9.9,
        "tsp": 3.3,
    },
    "semolina flour": {
        "cup": 167,
        "tbsp": 10.4,
        "tsp": 3.5,
    },
    "rye flour": {
        "cup": 102,
        "tbsp": 6.4,
        "tsp": 2.1,
    },

    # =========================================================================
    # SUGARS & SWEETENERS
    # =========================================================================
    "granulated sugar": {
        "cup": 200,
        "tbsp": 12.5,
        "tsp": 4.2,
    },
    "white sugar": {
        "cup": 200,
        "tbsp": 12.5,
        "tsp": 4.2,
        "alias_for": "granulated sugar"
    },
    "brown sugar packed": {
        "cup": 220,
        "tbsp": 13.8,
        "tsp": 4.6,
        "notes": "Firmly packed"
    },
    "brown sugar light packed": {
        "cup": 220,
        "tbsp": 13.8,
        "tsp": 4.6,
    },
    "brown sugar dark packed": {
        "cup": 220,
        "tbsp": 13.8,
        "tsp": 4.6,
    },
    "powdered sugar": {
        "cup": 120,
        "tbsp": 7.5,
        "tsp": 2.5,
        "notes": "Unsifted"
    },
    "confectioners sugar": {
        "cup": 120,
        "tbsp": 7.5,
        "tsp": 2.5,
        "alias_for": "powdered sugar"
    },
    "icing sugar": {
        "cup": 120,
        "tbsp": 7.5,
        "tsp": 2.5,
        "alias_for": "powdered sugar"
    },
    "honey": {
        "cup": 340,
        "tbsp": 21.3,
        "tsp": 7.1,
        "density_g_per_ml": 1.43
    },
    "maple syrup": {
        "cup": 322,
        "tbsp": 20.1,
        "tsp": 6.7,
        "density_g_per_ml": 1.36
    },
    "corn syrup": {
        "cup": 341,
        "tbsp": 21.3,
        "tsp": 7.1,
        "density_g_per_ml": 1.44
    },
    "molasses": {
        "cup": 337,
        "tbsp": 21.1,
        "tsp": 7.0,
        "density_g_per_ml": 1.42
    },
    "agave nectar": {
        "cup": 336,
        "tbsp": 21.0,
        "tsp": 7.0,
    },
    "stevia": {
        "tsp": 0.5,
        "notes": "Powdered stevia, very light"
    },

    # =========================================================================
    # FATS & OILS
    # =========================================================================
    "butter unsalted": {
        "cup": 227,
        "tbsp": 14.2,
        "tsp": 4.7,
        "stick": 113,
        "notes": "1 stick = 1/2 cup = 8 tbsp"
    },
    "butter salted": {
        "cup": 227,
        "tbsp": 14.2,
        "tsp": 4.7,
        "stick": 113,
    },
    "butter": {
        "cup": 227,
        "tbsp": 14.2,
        "tsp": 4.7,
        "stick": 113,
        "alias_for": "butter unsalted"
    },
    "vegetable oil": {
        "cup": 218,
        "tbsp": 13.6,
        "tsp": 4.5,
        "density_g_per_ml": 0.92
    },
    "canola oil": {
        "cup": 218,
        "tbsp": 13.6,
        "tsp": 4.5,
        "density_g_per_ml": 0.92
    },
    "olive oil": {
        "cup": 216,
        "tbsp": 13.5,
        "tsp": 4.5,
        "density_g_per_ml": 0.91
    },
    "coconut oil": {
        "cup": 218,
        "tbsp": 13.6,
        "tsp": 4.5,
    },
    "shortening": {
        "cup": 205,
        "tbsp": 12.8,
        "tsp": 4.3,
    },
    "lard": {
        "cup": 205,
        "tbsp": 12.8,
        "tsp": 4.3,
    },
    "margarine": {
        "cup": 227,
        "tbsp": 14.2,
        "tsp": 4.7,
    },

    # =========================================================================
    # DAIRY
    # =========================================================================
    "whole milk": {
        "cup": 244,
        "tbsp": 15.3,
        "tsp": 5.1,
        "density_g_per_ml": 1.03
    },
    "milk": {
        "cup": 244,
        "tbsp": 15.3,
        "tsp": 5.1,
        "alias_for": "whole milk"
    },
    "skim milk": {
        "cup": 245,
        "tbsp": 15.3,
        "tsp": 5.1,
    },
    "2% milk": {
        "cup": 244,
        "tbsp": 15.3,
        "tsp": 5.1,
    },
    "buttermilk": {
        "cup": 245,
        "tbsp": 15.3,
        "tsp": 5.1,
    },
    "heavy cream": {
        "cup": 238,
        "tbsp": 14.9,
        "tsp": 5.0,
    },
    "heavy whipping cream": {
        "cup": 238,
        "tbsp": 14.9,
        "tsp": 5.0,
        "alias_for": "heavy cream"
    },
    "light cream": {
        "cup": 240,
        "tbsp": 15.0,
        "tsp": 5.0,
    },
    "half and half": {
        "cup": 242,
        "tbsp": 15.1,
        "tsp": 5.0,
    },
    "sour cream": {
        "cup": 242,
        "tbsp": 15.1,
        "tsp": 5.0,
    },
    "cream cheese": {
        "cup": 232,
        "tbsp": 14.5,
        "tsp": 4.8,
    },
    "yogurt plain": {
        "cup": 245,
        "tbsp": 15.3,
        "tsp": 5.1,
    },
    "greek yogurt": {
        "cup": 280,
        "tbsp": 17.5,
        "tsp": 5.8,
    },
    "ricotta cheese": {
        "cup": 246,
        "tbsp": 15.4,
        "tsp": 5.1,
    },
    "cottage cheese": {
        "cup": 226,
        "tbsp": 14.1,
        "tsp": 4.7,
    },
    "parmesan grated": {
        "cup": 100,
        "tbsp": 6.3,
        "tsp": 2.1,
    },
    "cheddar cheese shredded": {
        "cup": 113,
        "tbsp": 7.1,
        "tsp": 2.4,
    },
    "mozzarella shredded": {
        "cup": 113,
        "tbsp": 7.1,
        "tsp": 2.4,
    },
    "evaporated milk": {
        "cup": 252,
        "tbsp": 15.8,
        "tsp": 5.3,
    },
    "sweetened condensed milk": {
        "cup": 306,
        "tbsp": 19.1,
        "tsp": 6.4,
    },

    # =========================================================================
    # EGGS
    # =========================================================================
    "egg whole large": {
        "whole": 50,
        "large": 50,
        "notes": "Without shell"
    },
    "egg whole medium": {
        "whole": 44,
        "medium": 44,
    },
    "egg whole small": {
        "whole": 38,
        "small": 38,
    },
    "egg whole extra large": {
        "whole": 56,
        "large": 56,
    },
    "egg whole jumbo": {
        "whole": 63,
        "large": 63,
    },
    "egg white large": {
        "whole": 33,
        "large": 33,
        "tbsp": 15,
    },
    "egg yolk large": {
        "whole": 17,
        "large": 17,
        "tbsp": 14,
    },
    "egg": {
        "whole": 50,
        "large": 50,
        "medium": 44,
        "small": 38,
        "alias_for": "egg whole large",
        "notes": "Defaults to large egg"
    },

    # =========================================================================
    # LEAVENERS & BAKING ESSENTIALS
    # =========================================================================
    "baking powder": {
        "tbsp": 13.8,
        "tsp": 4.6,
    },
    "baking soda": {
        "tbsp": 13.8,
        "tsp": 4.6,
    },
    "active dry yeast": {
        "tbsp": 8.5,
        "tsp": 2.8,
        "packet": 7,
        "notes": "1 packet = 2.25 tsp"
    },
    "instant yeast": {
        "tbsp": 8.5,
        "tsp": 2.8,
        "packet": 7,
    },
    "cream of tartar": {
        "tbsp": 9.4,
        "tsp": 3.1,
    },
    "salt": {
        "tbsp": 18,
        "tsp": 6,
    },
    "table salt": {
        "tbsp": 18,
        "tsp": 6,
        "alias_for": "salt"
    },
    "kosher salt": {
        "tbsp": 15,
        "tsp": 5,
        "notes": "Morton's kosher salt; Diamond Crystal is lighter"
    },
    "sea salt fine": {
        "tbsp": 18,
        "tsp": 6,
    },

    # =========================================================================
    # CHOCOLATE & COCOA
    # =========================================================================
    "cocoa powder unsweetened": {
        "cup": 85,
        "tbsp": 5.3,
        "tsp": 1.8,
    },
    "cocoa powder": {
        "cup": 85,
        "tbsp": 5.3,
        "tsp": 1.8,
        "alias_for": "cocoa powder unsweetened"
    },
    "dutch process cocoa": {
        "cup": 85,
        "tbsp": 5.3,
        "tsp": 1.8,
    },
    "chocolate chips": {
        "cup": 170,
        "tbsp": 10.6,
        "tsp": 3.5,
    },
    "chocolate chips semisweet": {
        "cup": 170,
        "tbsp": 10.6,
        "tsp": 3.5,
    },
    "chocolate chips milk": {
        "cup": 170,
        "tbsp": 10.6,
        "tsp": 3.5,
    },
    "chocolate chips white": {
        "cup": 170,
        "tbsp": 10.6,
        "tsp": 3.5,
    },
    "chocolate chopped": {
        "cup": 170,
        "tbsp": 10.6,
        "tsp": 3.5,
    },

    # =========================================================================
    # NUTS & SEEDS
    # =========================================================================
    "almonds whole": {
        "cup": 143,
        "tbsp": 8.9,
    },
    "almonds sliced": {
        "cup": 92,
        "tbsp": 5.8,
    },
    "almonds slivered": {
        "cup": 108,
        "tbsp": 6.8,
    },
    "walnuts chopped": {
        "cup": 120,
        "tbsp": 7.5,
    },
    "walnuts halves": {
        "cup": 100,
        "tbsp": 6.3,
    },
    "pecans chopped": {
        "cup": 109,
        "tbsp": 6.8,
    },
    "pecans halves": {
        "cup": 99,
        "tbsp": 6.2,
    },
    "peanuts": {
        "cup": 146,
        "tbsp": 9.1,
    },
    "cashews": {
        "cup": 137,
        "tbsp": 8.6,
    },
    "hazelnuts": {
        "cup": 135,
        "tbsp": 8.4,
    },
    "macadamia nuts": {
        "cup": 134,
        "tbsp": 8.4,
    },
    "pistachios shelled": {
        "cup": 123,
        "tbsp": 7.7,
    },
    "pine nuts": {
        "cup": 135,
        "tbsp": 8.4,
    },
    "sunflower seeds": {
        "cup": 140,
        "tbsp": 8.8,
    },
    "pumpkin seeds": {
        "cup": 129,
        "tbsp": 8.1,
    },
    "sesame seeds": {
        "cup": 144,
        "tbsp": 9.0,
        "tsp": 3.0,
    },
    "flax seeds": {
        "cup": 168,
        "tbsp": 10.5,
        "tsp": 3.5,
    },
    "chia seeds": {
        "cup": 170,
        "tbsp": 10.6,
        "tsp": 3.5,
    },
    "poppy seeds": {
        "tbsp": 8.8,
        "tsp": 2.9,
    },

    # =========================================================================
    # DRIED FRUITS
    # =========================================================================
    "raisins": {
        "cup": 145,
        "tbsp": 9.1,
    },
    "dried cranberries": {
        "cup": 120,
        "tbsp": 7.5,
    },
    "dried apricots chopped": {
        "cup": 130,
        "tbsp": 8.1,
    },
    "dates chopped": {
        "cup": 147,
        "tbsp": 9.2,
    },
    "dried cherries": {
        "cup": 140,
        "tbsp": 8.8,
    },
    "dried blueberries": {
        "cup": 140,
        "tbsp": 8.8,
    },
    "shredded coconut sweetened": {
        "cup": 93,
        "tbsp": 5.8,
    },
    "shredded coconut unsweetened": {
        "cup": 80,
        "tbsp": 5.0,
    },
    "coconut flakes": {
        "cup": 75,
        "tbsp": 4.7,
    },

    # =========================================================================
    # OATS & GRAINS
    # =========================================================================
    "rolled oats": {
        "cup": 80,
        "tbsp": 5.0,
    },
    "old fashioned oats": {
        "cup": 80,
        "tbsp": 5.0,
        "alias_for": "rolled oats"
    },
    "quick oats": {
        "cup": 80,
        "tbsp": 5.0,
    },
    "steel cut oats": {
        "cup": 160,
        "tbsp": 10.0,
    },
    "oat flour": {
        "cup": 92,
        "tbsp": 5.8,
    },
    "breadcrumbs dry": {
        "cup": 108,
        "tbsp": 6.8,
    },
    "breadcrumbs fresh": {
        "cup": 60,
        "tbsp": 3.8,
    },
    "panko breadcrumbs": {
        "cup": 60,
        "tbsp": 3.8,
    },
    "graham cracker crumbs": {
        "cup": 100,
        "tbsp": 6.3,
    },
    "cornmeal": {
        "cup": 157,
        "tbsp": 9.8,
        "tsp": 3.3,
    },
    "polenta": {
        "cup": 157,
        "tbsp": 9.8,
        "alias_for": "cornmeal"
    },

    # =========================================================================
    # EXTRACTS & FLAVORINGS
    # =========================================================================
    "vanilla extract": {
        "tbsp": 13,
        "tsp": 4.2,
    },
    "almond extract": {
        "tbsp": 13,
        "tsp": 4.2,
    },
    "lemon extract": {
        "tbsp": 13,
        "tsp": 4.2,
    },
    "peppermint extract": {
        "tbsp": 13,
        "tsp": 4.2,
    },
    "vanilla bean paste": {
        "tbsp": 18,
        "tsp": 6,
    },
    "espresso powder": {
        "tbsp": 5.3,
        "tsp": 1.8,
    },
    "instant coffee": {
        "tbsp": 5.3,
        "tsp": 1.8,
    },

    # =========================================================================
    # LIQUIDS
    # =========================================================================
    "water": {
        "cup": 237,
        "tbsp": 14.8,
        "tsp": 4.9,
        "density_g_per_ml": 1.0
    },
    "lemon juice": {
        "cup": 244,
        "tbsp": 15.3,
        "tsp": 5.1,
    },
    "lime juice": {
        "cup": 244,
        "tbsp": 15.3,
        "tsp": 5.1,
    },
    "orange juice": {
        "cup": 248,
        "tbsp": 15.5,
        "tsp": 5.2,
    },
    "apple cider vinegar": {
        "cup": 239,
        "tbsp": 14.9,
        "tsp": 5.0,
    },
    "white vinegar": {
        "cup": 238,
        "tbsp": 14.9,
        "tsp": 5.0,
    },
    "vegetable broth": {
        "cup": 240,
        "tbsp": 15.0,
        "tsp": 5.0,
    },

    # =========================================================================
    # PEANUT BUTTER & SPREADS
    # =========================================================================
    "peanut butter": {
        "cup": 258,
        "tbsp": 16.1,
        "tsp": 5.4,
    },
    "almond butter": {
        "cup": 258,
        "tbsp": 16.1,
        "tsp": 5.4,
    },
    "nutella": {
        "cup": 290,
        "tbsp": 18.1,
        "tsp": 6.0,
    },
    "tahini": {
        "cup": 240,
        "tbsp": 15.0,
        "tsp": 5.0,
    },

    # =========================================================================
    # SPICES (small quantities but needed)
    # =========================================================================
    "cinnamon ground": {
        "tbsp": 7.8,
        "tsp": 2.6,
    },
    "nutmeg ground": {
        "tbsp": 7.0,
        "tsp": 2.3,
    },
    "ginger ground": {
        "tbsp": 5.4,
        "tsp": 1.8,
    },
    "allspice ground": {
        "tbsp": 6.0,
        "tsp": 2.0,
    },
    "cloves ground": {
        "tbsp": 6.6,
        "tsp": 2.2,
    },
    "cardamom ground": {
        "tbsp": 5.8,
        "tsp": 1.9,
    },
    "pumpkin pie spice": {
        "tbsp": 6.0,
        "tsp": 2.0,
    },
    "apple pie spice": {
        "tbsp": 6.0,
        "tsp": 2.0,
    },

    # =========================================================================
    # FRESH PRODUCE (common in baking)
    # =========================================================================
    "banana mashed": {
        "cup": 225,
        "whole": 118,
        "medium": 118,
        "large": 136,
    },
    "applesauce": {
        "cup": 244,
        "tbsp": 15.3,
    },
    "pumpkin puree": {
        "cup": 245,
        "tbsp": 15.3,
    },
    "lemon zest": {
        "tbsp": 6,
        "tsp": 2,
    },
    "orange zest": {
        "tbsp": 6,
        "tsp": 2,
    },
    "raspberries fresh": {
        "cup": 123,
    },
    "blueberries fresh": {
        "cup": 148,
    },
    "strawberries sliced": {
        "cup": 166,
    },
}


# Aliases for common variations
INGREDIENT_ALIASES: dict[str, str] = {
    # Flour aliases
    "flour": "all-purpose flour",
    "ap flour": "all-purpose flour",
    "plain flour": "all-purpose flour",
    "white flour": "all-purpose flour",
    "self-rising flour": "all-purpose flour",  # Note: has leavening
    "self rising flour": "all-purpose flour",

    # Sugar aliases
    "sugar": "granulated sugar",
    "white sugar": "granulated sugar",
    "caster sugar": "granulated sugar",
    "superfine sugar": "granulated sugar",
    "light brown sugar": "brown sugar light packed",
    "dark brown sugar": "brown sugar dark packed",
    "brown sugar": "brown sugar packed",
    "confectioner's sugar": "powdered sugar",
    "icing sugar": "powdered sugar",
    "10x sugar": "powdered sugar",

    # Butter aliases
    "unsalted butter": "butter unsalted",
    "salted butter": "butter salted",
    "sweet cream butter": "butter unsalted",

    # Egg aliases
    "large egg": "egg whole large",
    "large eggs": "egg whole large",
    "eggs": "egg whole large",
    "egg": "egg whole large",
    "egg whites": "egg white large",
    "egg yolks": "egg yolk large",
    "egg white": "egg white large",
    "egg yolk": "egg yolk large",

    # Milk aliases
    "2 percent milk": "2% milk",
    "1 percent milk": "skim milk",
    "nonfat milk": "skim milk",
    "fat free milk": "skim milk",

    # Oil aliases
    "oil": "vegetable oil",
    "cooking oil": "vegetable oil",
    "neutral oil": "vegetable oil",
    "extra virgin olive oil": "olive oil",
    "evoo": "olive oil",

    # Other aliases
    "oats": "rolled oats",
    "quick cooking oats": "quick oats",
    "instant oats": "quick oats",
    "vanilla": "vanilla extract",
    "pure vanilla extract": "vanilla extract",
    "chocolate": "chocolate chips semisweet",
    "semi-sweet chocolate chips": "chocolate chips semisweet",
    "semisweet chocolate": "chocolate chips semisweet",
    "semisweet chocolate chips": "chocolate chips semisweet",
    "cocoa": "cocoa powder unsweetened",
    "unsweetened cocoa": "cocoa powder unsweetened",
    "natural cocoa powder": "cocoa powder unsweetened",
    "bittersweet chocolate": "chocolate chips semisweet",
    "white chocolate chips": "chocolate chips white",
    "milk chocolate chips": "chocolate chips milk",

    # Cream aliases
    "whipping cream": "heavy cream",
    "cream": "heavy cream",

    # Misc
    "cinnamon": "cinnamon ground",
    "nutmeg": "nutmeg ground",
    "ginger": "ginger ground",
    "baking cocoa": "cocoa powder unsweetened",
    "raspberries": "raspberries fresh",
    "blueberries": "blueberries fresh",
    "strawberries": "strawberries sliced",
}


# Unit conversion constants
ML_PER_CUP = 236.588
ML_PER_TBSP = 14.787
ML_PER_TSP = 4.929
ML_PER_FL_OZ = 29.574

# Pinch/dash estimates (very small amounts)
PINCH_GRAMS = 0.3  # ~1/16 tsp
DASH_GRAMS = 0.6   # ~1/8 tsp
