"""
LLM-based recipe parser for extracting structured ingredients from recipe text.
"""

import json
import re
from typing import Optional
from openai import AsyncOpenAI

from models.recipe import ParsedIngredient, RecipeInput, VolumeUnit
from config import settings


PARSE_PROMPT = """
Parse this recipe into structured ingredients. Extract each ingredient with its quantity and unit.

Recipe text:
{recipe_text}

Rules:
1. Normalize fractions: "1/2" → 0.5, "1/4" → 0.25, "3/4" → 0.75
2. Handle ranges by taking the average: "2-3 cups" → 2.5 cups
3. For "to taste" or unspecified amounts, use quantity: 0 and add a note
4. Separate compound ingredients: "1 cup flour + 1/2 cup sugar" → two ingredients
5. For items like "2 large eggs", use unit: "large" and quantity: 2
6. For items like "1 stick butter", use unit: "stick" and quantity: 1
7. For items like "1 (8 oz) package cream cheese", extract the weight: unit: "oz", quantity: 8
8. Ignore descriptors like "softened", "melted", "room temperature" - keep just the ingredient name
9. For packaged items with weights, prefer the weight measurement

Respond with JSON only:
{{
    "recipe_name": "<inferred name or 'Untitled Recipe'>",
    "ingredients": [
        {{
            "raw_text": "<original text>",
            "name": "<ingredient name without quantity/unit/descriptors>",
            "quantity": <number>,
            "unit": "<cup|tbsp|tsp|g|oz|lb|whole|large|medium|small|stick|piece|clove|pinch|dash|ml|l|packet>",
            "notes": "<any special notes like 'to taste', 'optional', etc.>"
        }}
    ],
    "yield_info": {{
        "quantity": <number or null>,
        "description": "<e.g., '24 cookies', '1 loaf', '12 servings'>"
    }},
    "parsing_notes": ["<any issues or ambiguities found>"]
}}
"""


class RecipeParser:
    """
    Parse recipe text into structured ingredients using LLM.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)

    async def parse_recipe_text(self, recipe_text: str, recipe_name: Optional[str] = None) -> RecipeInput:
        """
        Parse free-form recipe text into structured ingredients.

        Args:
            recipe_text: Raw recipe text with ingredients
            recipe_name: Optional recipe name (will be inferred if not provided)

        Returns:
            RecipeInput with parsed ingredients
        """
        prompt = PARSE_PROMPT.format(recipe_text=recipe_text)

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2000
        )

        response_text = response.choices[0].message.content
        if response_text is None:
            raise ValueError("Failed to parse recipe - no response from LLM")

        result = json.loads(response_text)

        # Convert to our models
        ingredients = []
        for item in result.get("ingredients", []):
            try:
                unit = self._normalize_unit(item.get("unit", "whole"))
                ingredient = ParsedIngredient(
                    raw_text=item.get("raw_text", ""),
                    name=item.get("name", "unknown"),
                    quantity=float(item.get("quantity", 0)),
                    unit=unit,
                )
                ingredients.append(ingredient)
            except (ValueError, KeyError) as e:
                # Skip malformed ingredients but continue parsing
                continue

        # Extract yield info
        yield_info = result.get("yield_info", {})

        return RecipeInput(
            name=recipe_name or result.get("recipe_name", "Untitled Recipe"),
            raw_text=recipe_text,
            ingredients=ingredients,
            yield_quantity=yield_info.get("quantity"),
            yield_description=yield_info.get("description"),
        )

    def _normalize_unit(self, unit: str) -> VolumeUnit:
        """Convert string unit to VolumeUnit enum."""
        unit = unit.lower().strip()

        unit_map = {
            "cup": VolumeUnit.CUP,
            "cups": VolumeUnit.CUP,
            "c": VolumeUnit.CUP,
            "tbsp": VolumeUnit.TABLESPOON,
            "tablespoon": VolumeUnit.TABLESPOON,
            "tablespoons": VolumeUnit.TABLESPOON,
            "tsp": VolumeUnit.TEASPOON,
            "teaspoon": VolumeUnit.TEASPOON,
            "teaspoons": VolumeUnit.TEASPOON,
            "g": VolumeUnit.GRAM,
            "gram": VolumeUnit.GRAM,
            "grams": VolumeUnit.GRAM,
            "kg": VolumeUnit.KILOGRAM,
            "kilogram": VolumeUnit.KILOGRAM,
            "oz": VolumeUnit.OUNCE,
            "ounce": VolumeUnit.OUNCE,
            "ounces": VolumeUnit.OUNCE,
            "lb": VolumeUnit.POUND,
            "pound": VolumeUnit.POUND,
            "pounds": VolumeUnit.POUND,
            "whole": VolumeUnit.WHOLE,
            "large": VolumeUnit.LARGE,
            "medium": VolumeUnit.MEDIUM,
            "small": VolumeUnit.SMALL,
            "stick": VolumeUnit.STICK,
            "sticks": VolumeUnit.STICK,
            "piece": VolumeUnit.PIECE,
            "pieces": VolumeUnit.PIECE,
            "clove": VolumeUnit.CLOVE,
            "cloves": VolumeUnit.CLOVE,
            "pinch": VolumeUnit.PINCH,
            "dash": VolumeUnit.DASH,
            "ml": VolumeUnit.MILLILITER,
            "milliliter": VolumeUnit.MILLILITER,
            "l": VolumeUnit.LITER,
            "liter": VolumeUnit.LITER,
            "packet": VolumeUnit.PACKET,
            "packets": VolumeUnit.PACKET,
            "slice": VolumeUnit.SLICE,
            "slices": VolumeUnit.SLICE,
            "fl_oz": VolumeUnit.FLUID_OUNCE,
            "fluid ounce": VolumeUnit.FLUID_OUNCE,
        }

        return unit_map.get(unit, VolumeUnit.WHOLE)

    def parse_ingredient_line(self, line: str) -> Optional[ParsedIngredient]:
        """
        Parse a single ingredient line using regex patterns.

        This is a fallback for simple cases without LLM.
        """
        line = line.strip()
        if not line:
            return None

        # Common patterns
        patterns = [
            # "2 cups all-purpose flour"
            r'^([\d./\s]+)\s+(cups?|tbsp|tablespoons?|tsp|teaspoons?|oz|ounces?|lb|pounds?|g|grams?|ml|l)\s+(.+)$',
            # "3 large eggs"
            r'^(\d+)\s+(large|medium|small|whole)\s+(.+)$',
            # "1 stick butter"
            r'^([\d./]+)\s+(sticks?|cloves?|pieces?|packets?|slices?)\s+(.+)$',
            # "pinch of salt"
            r'^(pinch|dash)\s+(?:of\s+)?(.+)$',
        ]

        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()

                if len(groups) == 3:
                    qty_str, unit, name = groups
                    quantity = self._parse_quantity(qty_str)
                elif len(groups) == 2:
                    unit, name = groups
                    quantity = 1
                else:
                    continue

                return ParsedIngredient(
                    raw_text=line,
                    name=name.strip(),
                    quantity=quantity,
                    unit=self._normalize_unit(unit)
                )

        return None

    def _parse_quantity(self, qty_str: str) -> float:
        """Parse quantity string including fractions."""
        qty_str = qty_str.strip()

        # Handle Unicode fractions
        unicode_fractions = {
            '½': 0.5, '⅓': 1/3, '⅔': 2/3, '¼': 0.25, '¾': 0.75,
            '⅕': 0.2, '⅖': 0.4, '⅗': 0.6, '⅘': 0.8,
            '⅙': 1/6, '⅚': 5/6, '⅛': 0.125, '⅜': 0.375, '⅝': 0.625, '⅞': 0.875
        }

        has_unicode_fraction = False
        for char, value in unicode_fractions.items():
            if char in qty_str:
                # Handle "1½" → "1 0.5"
                qty_str = qty_str.replace(char, f" {value}")
                has_unicode_fraction = True

        # If we replaced unicode fractions, sum the parts
        if has_unicode_fraction:
            parts = qty_str.split()
            total = 0.0
            for part in parts:
                try:
                    total += float(part)
                except ValueError:
                    pass
            return total if total > 0 else 1.0

        # Handle text fractions
        if '/' in qty_str:
            parts = qty_str.split()
            total = 0
            for part in parts:
                if '/' in part:
                    try:
                        num, denom = part.split('/')
                        total += float(num) / float(denom)
                    except (ValueError, ZeroDivisionError):
                        pass
                else:
                    try:
                        total += float(part)
                    except ValueError:
                        pass
            return total if total > 0 else 1.0

        # Handle ranges (take average)
        if '-' in qty_str:
            try:
                parts = qty_str.split('-')
                values = [float(p.strip()) for p in parts if p.strip()]
                return sum(values) / len(values) if values else 1.0
            except ValueError:
                pass

        try:
            return float(qty_str)
        except ValueError:
            return 1.0
