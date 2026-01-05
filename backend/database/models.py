"""
SQLAlchemy models for USDA caching.
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class USDAFood(Base):
    """Cached USDA food items."""
    __tablename__ = "usda_foods"

    fdc_id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False, index=True)
    data_type = Column(String)  # Foundation, SR Legacy, Branded, Survey
    brand_owner = Column(String)
    ingredients = Column(Text)
    serving_size = Column(Float)
    serving_size_unit = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    nutrients = relationship(
        "USDANutrition",
        back_populates="food",
        cascade="all, delete-orphan"
    )


class USDANutrition(Base):
    """Cached nutrition data per 100g for USDA foods."""
    __tablename__ = "usda_nutrition"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fdc_id = Column(Integer, ForeignKey("usda_foods.fdc_id"), nullable=False)
    nutrient_name = Column(String, nullable=False)
    nutrient_id = Column(Integer)  # USDA's nutrient ID
    amount = Column(Float)
    unit = Column(String)

    food = relationship("USDAFood", back_populates="nutrients")


class USDASearchCache(Base):
    """Cache of USDA search query results."""
    __tablename__ = "usda_search_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String, nullable=False)
    query_hash = Column(String, unique=True, nullable=False)
    result_fdc_ids = Column(Text)  # JSON array
    total_hits = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class CacheStats(Base):
    """Statistics for cache performance tracking."""
    __tablename__ = "cache_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String, nullable=False)  # hit, miss, refresh
    query = Column(String)
    fdc_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
