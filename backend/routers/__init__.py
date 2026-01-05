from .extract import router as extract_router
from .calculate import router as calculate_router
from .label import router as label_router
from .usda import router as usda_router
from .recipe import router as recipe_router

__all__ = ["extract_router", "calculate_router", "label_router", "usda_router", "recipe_router"]
