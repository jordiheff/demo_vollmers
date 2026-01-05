"""
Low-level USDA FoodData Central API client.
"""

import httpx
from typing import Optional
from .usda_constants import USDA_NUTRIENT_MAP, FDA_REQUIRED_NUTRIENTS
from .usda_errors import USDAAPIError, USDAErrorType, handle_usda_response


class USDAAPIClient:
    """
    Low-level client for USDA FoodData Central API.

    This client handles raw API communication. For caching,
    use USDAClient from usda_cache.py which wraps this client.
    """

    BASE_URL = "https://api.nal.usda.gov/fdc/v1"
    DEFAULT_TIMEOUT = 30.0

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("USDA API key is required")
        self.api_key = api_key

    async def search(
        self,
        query: str,
        data_types: Optional[list[str]] = None,
        page_size: int = 25,
        page_number: int = 1,
        brand_owner: Optional[str] = None
    ) -> dict:
        """
        Search for foods in USDA database.

        Args:
            query: Search terms
            data_types: Filter by type (Foundation, SR Legacy, Branded, Survey)
            page_size: Results per page (max 200)
            page_number: Page number (1-indexed)
            brand_owner: Filter by brand name

        Returns:
            Raw API response dict with foods and pagination info
        """
        params = {
            "api_key": self.api_key,
            "query": query,
            "pageSize": min(page_size, 200),
            "pageNumber": page_number,
        }

        if data_types:
            params["dataType"] = data_types
        if brand_owner:
            params["brandOwner"] = brand_owner

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/foods/search",
                    params=params,
                    timeout=self.DEFAULT_TIMEOUT
                )
                return handle_usda_response(response)
        except httpx.TimeoutException:
            raise USDAAPIError(
                USDAErrorType.TIMEOUT,
                "USDA API request timed out"
            )
        except httpx.RequestError as e:
            raise USDAAPIError(
                USDAErrorType.NETWORK_ERROR,
                f"Network error: {str(e)}"
            )

    async def get_food(
        self,
        fdc_id: int,
        format: str = "full",
        nutrients: Optional[list[int]] = None
    ) -> dict:
        """
        Get detailed nutrition data for a specific food.

        Args:
            fdc_id: USDA FoodData Central ID
            format: "full" or "abridged"
            nutrients: List of nutrient IDs to include (None = all)

        Returns:
            Raw API response dict with full food details
        """
        params = {
            "api_key": self.api_key,
            "format": format,
        }

        if nutrients:
            params["nutrients"] = nutrients

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/food/{fdc_id}",
                    params=params,
                    timeout=self.DEFAULT_TIMEOUT
                )
                return handle_usda_response(response)
        except httpx.TimeoutException:
            raise USDAAPIError(
                USDAErrorType.TIMEOUT,
                "USDA API request timed out"
            )
        except httpx.RequestError as e:
            raise USDAAPIError(
                USDAErrorType.NETWORK_ERROR,
                f"Network error: {str(e)}"
            )

    async def get_foods_batch(
        self,
        fdc_ids: list[int],
        format: str = "abridged",
        nutrients: Optional[list[int]] = None
    ) -> list[dict]:
        """
        Get multiple foods in a single request.

        Args:
            fdc_ids: List of USDA FoodData Central IDs (max 20)
            format: "full" or "abridged"
            nutrients: List of nutrient IDs to include

        Returns:
            List of food detail dicts
        """
        if len(fdc_ids) > 20:
            raise ValueError("Maximum 20 foods per batch request")

        body = {
            "fdcIds": fdc_ids,
            "format": format,
        }

        if nutrients:
            body["nutrients"] = nutrients

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/foods",
                    params={"api_key": self.api_key},
                    json=body,
                    timeout=self.DEFAULT_TIMEOUT
                )
                return handle_usda_response(response)
        except httpx.TimeoutException:
            raise USDAAPIError(
                USDAErrorType.TIMEOUT,
                "USDA API request timed out"
            )
        except httpx.RequestError as e:
            raise USDAAPIError(
                USDAErrorType.NETWORK_ERROR,
                f"Network error: {str(e)}"
            )

    async def get_food_for_label(self, fdc_id: int) -> dict:
        """
        Get food with only FDA-required nutrients.

        Convenience method that requests only the nutrients
        needed for nutrition label generation.
        """
        return await self.get_food(
            fdc_id,
            format="full",
            nutrients=FDA_REQUIRED_NUTRIENTS
        )

    def parse_nutrients(self, food_data: dict) -> dict:
        """
        Parse USDA food response into our nutrition schema.

        Args:
            food_data: Raw response from get_food()

        Returns:
            Dict with nutrition values mapped to our field names
        """
        result = {}

        for nutrient in food_data.get("foodNutrients", []):
            nutrient_info = nutrient.get("nutrient", {})
            nutrient_id = nutrient_info.get("id")

            if nutrient_id in USDA_NUTRIENT_MAP:
                field_name, expected_unit = USDA_NUTRIENT_MAP[nutrient_id]
                amount = nutrient.get("amount")

                if amount is not None:
                    result[field_name] = amount

        return result

    def parse_portions(self, food_data: dict) -> list[dict]:
        """
        Parse portion/serving size information.

        Args:
            food_data: Raw response from get_food()

        Returns:
            List of portion options with gram weights
        """
        portions = []

        for portion in food_data.get("foodPortions", []):
            portions.append({
                "gram_weight": portion.get("gramWeight"),
                "amount": portion.get("amount"),
                "unit": portion.get("measureUnit", {}).get("name"),
                "description": portion.get("modifier"),
            })

        return portions
