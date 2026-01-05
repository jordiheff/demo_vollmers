from pydantic import BaseModel
from typing import Optional
from enum import Enum


class FlagType(str, Enum):
    """Types of flags that can be applied to extracted data."""
    MISSING = "missing"              # Required field not found
    LOW_CONFIDENCE = "low_confidence"  # LLM uncertain about extraction
    CONVERTED = "converted"          # Unit conversion applied
    ANOMALY = "anomaly"              # Value outside expected range
    INFERRED = "inferred"            # Value derived, not directly stated


class ExtractionFlag(BaseModel):
    """Flag indicating an issue or note about extracted data."""
    field: str                       # Which nutrition field
    flag_type: FlagType
    message: str                     # Human-readable explanation
    original_value: Optional[str] = None  # Original text before conversion
    confidence: Optional[float] = None    # 0.0-1.0 if applicable
