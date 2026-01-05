"""
USDA FoodData Central caching layer.
"""

import hashlib
import json
import httpx
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database.models import USDAFood, USDANutrition, USDASearchCache, CacheStats
from models.nutrition import NutritionPer100g
from config import settings


class USDAClient:
    """Client for USDA FoodData Central API with caching."""

    BASE_URL = "https://api.nal.usda.gov/fdc/v1"

    # Map USDA nutrient IDs to our schema fields
    NUTRIENT_MAP = {
        1008: "calories",           # Energy (kcal)
        1003: "protein_g",          # Protein
        1004: "total_fat_g",        # Total lipid (fat)
        1258: "saturated_fat_g",    # Fatty acids, saturated
        1257: "trans_fat_g",        # Fatty acids, trans
        1253: "cholesterol_mg",     # Cholesterol
        1093: "sodium_mg",          # Sodium
        1005: "total_carbohydrate_g",  # Carbohydrate
        1079: "dietary_fiber_g",    # Fiber, total dietary
        2000: "total_sugars_g",     # Sugars, total
        1235: "added_sugars_g",     # Sugars, added
        1114: "vitamin_d_mcg",      # Vitamin D (D2 + D3)
        1087: "calcium_mg",         # Calcium
        1089: "iron_mg",            # Iron
        1092: "potassium_mg",       # Potassium
    }

    def __init__(self, api_key: str, db_session: Session):
        self.api_key = api_key
        self.db = db_session
        self.cache_expiry_days = settings.usda_cache_expiry_days

    def _hash_query(self, query: str) -> str:
        """Create consistent hash for search queries."""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()

    def _log_stat(self, event_type: str, query: str = None, fdc_id: int = None):
        """Log cache hit/miss for analytics."""
        stat = CacheStats(event_type=event_type, query=query, fdc_id=fdc_id)
        self.db.add(stat)
        self.db.commit()

    def _is_cache_fresh(self, created_at: datetime) -> bool:
        """Check if cached data is still valid."""
        expiry = created_at + timedelta(days=self.cache_expiry_days)
        return datetime.utcnow() < expiry

    async def search(
        self,
        query: str,
        data_types: list[str] = None,
        page_size: int = 25
    ) -> list[dict]:
        """
        Search for foods by name. Returns cached results if available.

        Args:
            query: Search term (e.g., "all-purpose flour")
            data_types: Filter by data type (e.g., ["Foundation", "SR Legacy"])
            page_size: Number of results to return

        Returns:
            List of food items with basic info
        """
        query_hash = self._hash_query(query)

        # Check cache first
        cached = self.db.query(USDASearchCache).filter_by(query_hash=query_hash).first()

        if cached and self._is_cache_fresh(cached.created_at):
            self._log_stat("hit", query=query)
            fdc_ids = json.loads(cached.result_fdc_ids)
            foods = self.db.query(USDAFood).filter(USDAFood.fdc_id.in_(fdc_ids)).all()
            return [self._food_to_dict(f) for f in foods]

        # Cache miss - fetch from API
        self._log_stat("miss", query=query)

        # Use headers for API key instead of query params (security best practice)
        headers = {"X-Api-Key": self.api_key}
        params = {
            "query": query,
            "pageSize": page_size,
        }
        if data_types:
            params["dataType"] = data_types

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/foods/search",
                params=params,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

        # Cache the results
        fdc_ids = []
        for item in data.get("foods", []):
            fdc_id = item["fdcId"]
            fdc_ids.append(fdc_id)

            # Upsert food record
            food = self.db.query(USDAFood).filter_by(fdc_id=fdc_id).first()
            if not food:
                food = USDAFood(
                    fdc_id=fdc_id,
                    description=item.get("description"),
                    data_type=item.get("dataType"),
                    brand_owner=item.get("brandOwner"),
                    ingredients=item.get("ingredients"),
                )
                self.db.add(food)

        # Cache the search results
        if cached:
            cached.result_fdc_ids = json.dumps(fdc_ids)
            cached.total_hits = data.get("totalHits", 0)
            cached.created_at = datetime.utcnow()
        else:
            cached = USDASearchCache(
                query=query.lower().strip(),
                query_hash=query_hash,
                result_fdc_ids=json.dumps(fdc_ids),
                total_hits=data.get("totalHits", 0)
            )
            self.db.add(cached)

        self.db.commit()

        return [self._food_to_dict(item) for item in data.get("foods", [])]

    async def get_nutrition(self, fdc_id: int) -> Optional[NutritionPer100g]:
        """
        Get full nutrition data for a specific food.

        Args:
            fdc_id: USDA FoodData Central ID

        Returns:
            NutritionPer100g object or None if not found
        """
        # Check cache first
        cached_nutrients = self.db.query(USDANutrition).filter_by(fdc_id=fdc_id).all()

        if cached_nutrients:
            food = self.db.query(USDAFood).filter_by(fdc_id=fdc_id).first()
            if food and self._is_cache_fresh(food.updated_at):
                self._log_stat("hit", fdc_id=fdc_id)
                return self._nutrients_to_model(cached_nutrients)

        # Cache miss - fetch from API
        self._log_stat("miss", fdc_id=fdc_id)

        # Use headers for API key instead of query params (security best practice)
        headers = {"X-Api-Key": self.api_key}

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/food/{fdc_id}",
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()

        # Update food record
        food = self.db.query(USDAFood).filter_by(fdc_id=fdc_id).first()
        if not food:
            food = USDAFood(fdc_id=fdc_id, description=data.get("description"))
            self.db.add(food)

        food.data_type = data.get("dataType")
        food.brand_owner = data.get("brandOwner")
        food.ingredients = data.get("ingredients")
        food.updated_at = datetime.utcnow()

        # Clear old nutrients and add new ones
        self.db.query(USDANutrition).filter_by(fdc_id=fdc_id).delete()

        for nutrient in data.get("foodNutrients", []):
            nutrient_data = nutrient.get("nutrient", {})
            nutrition = USDANutrition(
                fdc_id=fdc_id,
                nutrient_name=nutrient_data.get("name"),
                nutrient_id=nutrient_data.get("id"),
                amount=nutrient.get("amount"),
                unit=nutrient_data.get("unitName")
            )
            self.db.add(nutrition)

        self.db.commit()

        # Fetch fresh from DB and convert
        cached_nutrients = self.db.query(USDANutrition).filter_by(fdc_id=fdc_id).all()
        return self._nutrients_to_model(cached_nutrients)

    def _food_to_dict(self, food) -> dict:
        """Convert food record/dict to response format."""
        if isinstance(food, USDAFood):
            return {
                "fdc_id": food.fdc_id,
                "description": food.description,
                "data_type": food.data_type,
                "brand_owner": food.brand_owner,
            }
        # Raw API response
        return {
            "fdc_id": food.get("fdcId"),
            "description": food.get("description"),
            "data_type": food.get("dataType"),
            "brand_owner": food.get("brandOwner"),
        }

    def _nutrients_to_model(self, nutrients: list[USDANutrition]) -> NutritionPer100g:
        """Convert cached nutrients to NutritionPer100g model."""
        data = {}

        for nutrient in nutrients:
            if nutrient.nutrient_id in self.NUTRIENT_MAP:
                field_name = self.NUTRIENT_MAP[nutrient.nutrient_id]
                data[field_name] = nutrient.amount

        return NutritionPer100g(**data)

    def get_cache_stats(self) -> dict:
        """Get cache performance statistics."""
        total = self.db.query(CacheStats).count()
        hits = self.db.query(CacheStats).filter_by(event_type="hit").count()
        misses = self.db.query(CacheStats).filter_by(event_type="miss").count()

        cached_foods = self.db.query(USDAFood).count()
        cached_searches = self.db.query(USDASearchCache).count()

        return {
            "total_requests": total,
            "cache_hits": hits,
            "cache_misses": misses,
            "hit_rate": hits / total if total > 0 else 0,
            "cached_foods": cached_foods,
            "cached_searches": cached_searches,
        }

    def clear_expired_cache(self):
        """Remove expired cache entries."""
        expiry_date = datetime.utcnow() - timedelta(days=self.cache_expiry_days)

        # Clear old search caches
        self.db.query(USDASearchCache).filter(
            USDASearchCache.created_at < expiry_date
        ).delete()

        # Clear old food records (and their nutrients via cascade)
        self.db.query(USDAFood).filter(
            USDAFood.updated_at < expiry_date
        ).delete()

        self.db.commit()
