-- Initial database schema for USDA caching
-- Note: SQLAlchemy will auto-create these tables, this is for reference

-- Cache of USDA food search results
CREATE TABLE IF NOT EXISTS usda_foods (
    fdc_id INTEGER PRIMARY KEY,           -- USDA FoodData Central ID
    description TEXT NOT NULL,            -- Food name/description
    data_type TEXT,                        -- "Foundation", "SR Legacy", "Branded", etc.
    brand_owner TEXT,                      -- Brand name if applicable
    ingredients TEXT,                      -- Ingredient list if available
    serving_size REAL,                     -- Serving size in grams
    serving_size_unit TEXT,               -- Usually "g"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Nutrition data per 100g for cached foods
CREATE TABLE IF NOT EXISTS usda_nutrition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fdc_id INTEGER NOT NULL,
    nutrient_name TEXT NOT NULL,          -- e.g., "Total Fat", "Sodium"
    nutrient_id INTEGER,                  -- USDA nutrient ID
    amount REAL,                          -- Value per 100g
    unit TEXT,                            -- "g", "mg", "mcg", "kcal", etc.
    FOREIGN KEY (fdc_id) REFERENCES usda_foods(fdc_id),
    UNIQUE(fdc_id, nutrient_id)
);

-- Search query cache (maps search terms to results)
CREATE TABLE IF NOT EXISTS usda_search_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,                  -- Normalized search term
    query_hash TEXT NOT NULL UNIQUE,      -- MD5 hash for fast lookup
    result_fdc_ids TEXT,                  -- JSON array of fdc_ids
    total_hits INTEGER,                   -- Total results from USDA
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_foods_description ON usda_foods(description);
CREATE INDEX IF NOT EXISTS idx_nutrition_fdc_id ON usda_nutrition(fdc_id);
CREATE INDEX IF NOT EXISTS idx_search_hash ON usda_search_cache(query_hash);

-- Track cache statistics
CREATE TABLE IF NOT EXISTS cache_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,             -- "hit", "miss", "refresh"
    query TEXT,
    fdc_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
