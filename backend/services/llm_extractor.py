"""
LLM-powered nutrition data extraction using OpenAI GPT-4o Vision.
"""

import json
from typing import Optional, List
from openai import AsyncOpenAI

from models.nutrition import NutritionPer100g, ExtractedProduct
from models.flags import FlagType, ExtractionFlag
from config import settings


# System prompt for nutrition extraction
EXTRACTION_SYSTEM_PROMPT = """You are a nutrition data extraction specialist. Extract nutritional information
from food product specification sheets into a structured JSON format.

IMPORTANT GUIDELINES:
1. Look at the document carefully - nutrition values are in a TABLE format
2. Match each nutrient LABEL with its corresponding VALUE in the same row
3. All nutritional values should be per 100 grams
4. If a value is not found, set it to null - do NOT guess or infer
5. Pay attention to units (g, mg, mcg, IU) and include them in your understanding
6. Extract product name, code, ingredients list, and allergens if present

COMMON LABEL MAPPINGS:
- "Fat" or "Total Fat" → total_fat_g
- "Saturated Fat" → saturated_fat_g
- "Trans Fat" → trans_fat_g
- "Cholesterol" → cholesterol_mg
- "Sodium" → sodium_mg
- "Total Carbohydrate" or "Carbohydrate" → total_carbohydrate_g
- "Dietary Fiber" or "Total Fiber" or "Fiber" → dietary_fiber_g
- "Sugar" or "Total Sugars" → total_sugars_g
- "Protein" → protein_g
- "Vitamin D" → vitamin_d_mcg (convert IU if needed: IU ÷ 40 = mcg)
- "Calcium" → calcium_mg
- "Iron" → iron_mg
- "Potassium" → potassium_mg

OUTPUT FORMAT:
{
  "product_name": string or null,
  "product_code": string or null,
  "nutrition_per_100g": {
    "calories": number or null,
    "total_fat_g": number or null,
    "saturated_fat_g": number or null,
    "trans_fat_g": number or null,
    "cholesterol_mg": number or null,
    "sodium_mg": number or null,
    "total_carbohydrate_g": number or null,
    "dietary_fiber_g": number or null,
    "total_sugars_g": number or null,
    "added_sugars_g": number or null,
    "protein_g": number or null,
    "vitamin_d_mcg": number or null,
    "calcium_mg": number or null,
    "iron_mg": number or null,
    "potassium_mg": number or null
  },
  "ingredients_list": string or null,
  "allergens": [string],
  "extraction_notes": [
    {
      "field": string,
      "note": string,
      "confidence": "high" | "medium" | "low"
    }
  ]
}"""


class LLMExtractor:
    """Extract nutrition data from images using OpenAI GPT-4o Vision."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM extractor.

        Args:
            api_key: OpenAI API key. If not provided, uses settings.
        """
        self.client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)

    async def extract_from_images(self, images_base64: List[str]) -> ExtractedProduct:
        """
        Extract nutrition data from images using GPT-4o Vision.

        This is the preferred method as it preserves table structure.

        Args:
            images_base64: List of base64-encoded PNG images

        Returns:
            ExtractedProduct with nutrition data and flags
        """
        # Build content with images
        content = [
            {
                "type": "text",
                "text": "Extract the nutrition data from this food product specification sheet. Look carefully at the table and match each nutrient label with its value. Return the data as JSON."
            }
        ]

        # Add images
        for img_base64 in images_base64:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_base64}",
                    "detail": "high"
                }
            })

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": content}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2000
        )

        # Parse the response
        response_text = response.choices[0].message.content

        if response_text is None:
            # Handle case where model returns no content (e.g., content filtered or no data found)
            raise ValueError(
                "Could not extract nutrition data from this document. "
                "Please ensure it contains a nutrition facts table or per-100g nutritional values."
            )

        data = json.loads(response_text)

        return self._build_product(data)

    async def extract(self, text: str) -> ExtractedProduct:
        """
        Extract nutrition data from text using LLM.

        NOTE: For documents with tables, use extract_from_images() instead.

        Args:
            text: Raw text extracted from spec sheet

        Returns:
            ExtractedProduct with nutrition data and flags
        """
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract nutrition data from this spec sheet:\n\n{text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2000
        )

        response_text = response.choices[0].message.content

        if response_text is None:
            raise ValueError(
                "Could not extract nutrition data from this document. "
                "Please ensure it contains a nutrition facts table or per-100g nutritional values."
            )

        data = json.loads(response_text)

        return self._build_product(data, raw_text=text[:5000])

    def _build_product(self, data: dict, raw_text: Optional[str] = None) -> ExtractedProduct:
        """
        Build ExtractedProduct from parsed LLM response.

        Args:
            data: Parsed JSON from LLM
            raw_text: Optional raw text for debugging

        Returns:
            ExtractedProduct with nutrition data and flags
        """
        # Build nutrition model
        nutrition_data = data.get("nutrition_per_100g", {})
        nutrition = NutritionPer100g(
            calories=nutrition_data.get("calories"),
            total_fat_g=nutrition_data.get("total_fat_g"),
            saturated_fat_g=nutrition_data.get("saturated_fat_g"),
            trans_fat_g=nutrition_data.get("trans_fat_g"),
            cholesterol_mg=nutrition_data.get("cholesterol_mg"),
            sodium_mg=nutrition_data.get("sodium_mg"),
            total_carbohydrate_g=nutrition_data.get("total_carbohydrate_g"),
            dietary_fiber_g=nutrition_data.get("dietary_fiber_g"),
            total_sugars_g=nutrition_data.get("total_sugars_g"),
            added_sugars_g=nutrition_data.get("added_sugars_g"),
            protein_g=nutrition_data.get("protein_g"),
            vitamin_d_mcg=nutrition_data.get("vitamin_d_mcg"),
            calcium_mg=nutrition_data.get("calcium_mg"),
            iron_mg=nutrition_data.get("iron_mg"),
            potassium_mg=nutrition_data.get("potassium_mg"),
        )

        # Build flags from extraction notes
        flags = []
        for note in data.get("extraction_notes", []):
            confidence_map = {"high": 0.9, "medium": 0.7, "low": 0.4}
            confidence = confidence_map.get(note.get("confidence", "medium"), 0.7)

            if confidence < 0.7:
                flag_type = FlagType.LOW_CONFIDENCE
            else:
                flag_type = FlagType.INFERRED

            flags.append(ExtractionFlag(
                field=note.get("field", "unknown"),
                flag_type=flag_type,
                message=note.get("note", ""),
                confidence=confidence
            ))

        # Check for missing required fields
        required_fields = [
            ("calories", "Calories"),
            ("total_fat_g", "Total Fat"),
            ("sodium_mg", "Sodium"),
            ("total_carbohydrate_g", "Total Carbohydrate"),
            ("protein_g", "Protein"),
        ]

        for field, name in required_fields:
            if getattr(nutrition, field) is None:
                flags.append(ExtractionFlag(
                    field=field,
                    flag_type=FlagType.MISSING,
                    message=f"{name} not found in document"
                ))

        return ExtractedProduct(
            product_name=data.get("product_name"),
            product_code=data.get("product_code"),
            nutrition=nutrition,
            ingredients_list=data.get("ingredients_list"),
            allergens=data.get("allergens", []),
            flags=flags,
            raw_text=raw_text
        )
