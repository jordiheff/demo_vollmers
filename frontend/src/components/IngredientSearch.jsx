import React, { useState, useCallback } from 'react'
import { searchUSDAFoods, getUSDAFoodNutrition } from '../api/client'

const DATA_TYPES = [
  { value: 'Foundation', label: 'Foundation (Recommended)' },
  { value: 'SR Legacy', label: 'Standard Reference' },
  { value: 'Branded', label: 'Branded Products' },
  { value: 'Survey', label: 'Survey (FNDDS)' },
]

function IngredientSearch({ onIngredientSelect }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedTypes, setSelectedTypes] = useState(['Foundation', 'SR Legacy'])
  const [loadingNutrition, setLoadingNutrition] = useState(null)

  const handleSearch = useCallback(async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    setResults([])

    try {
      const foods = await searchUSDAFoods(query, {
        dataTypes: selectedTypes.length ? selectedTypes : undefined,
        pageSize: 25,
      })
      setResults(foods)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [query, selectedTypes])

  const handleSelectFood = useCallback(async (food) => {
    setLoadingNutrition(food.fdc_id)
    setError(null)

    try {
      const { description, nutrition } = await getUSDAFoodNutrition(food.fdc_id)
      onIngredientSelect({
        fdc_id: food.fdc_id,
        description: description || food.description,
        data_type: food.data_type,
        brand_owner: food.brand_owner,
        nutrition,
      })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingNutrition(null)
    }
  }, [onIngredientSelect])

  const toggleDataType = (type) => {
    setSelectedTypes((prev) =>
      prev.includes(type)
        ? prev.filter((t) => t !== type)
        : [...prev, type]
    )
  }

  return (
    <div className="ingredient-search">
      <form onSubmit={handleSearch} className="search-form">
        <div className="search-input-group">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search ingredients (e.g., all-purpose flour, butter)"
            className="search-input"
            disabled={loading}
          />
          <button type="submit" className="search-button" disabled={loading || !query.trim()}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        <div className="data-type-filters">
          <span className="filter-label">Data sources:</span>
          {DATA_TYPES.map((type) => (
            <label key={type.value} className="filter-checkbox">
              <input
                type="checkbox"
                checked={selectedTypes.includes(type.value)}
                onChange={() => toggleDataType(type.value)}
              />
              {type.label}
            </label>
          ))}
        </div>
      </form>

      {error && (
        <div className="search-error">
          {error}
        </div>
      )}

      {results.length > 0 && (
        <div className="search-results">
          <h4>Results ({results.length})</h4>
          <ul className="results-list">
            {results.map((food) => (
              <li key={food.fdc_id} className="result-item">
                <div className="result-info">
                  <span className="result-name">{food.description}</span>
                  <span className="result-meta">
                    {food.data_type}
                    {food.brand_owner && ` - ${food.brand_owner}`}
                  </span>
                </div>
                <button
                  onClick={() => handleSelectFood(food)}
                  disabled={loadingNutrition === food.fdc_id}
                  className="select-button"
                >
                  {loadingNutrition === food.fdc_id ? 'Loading...' : 'Add'}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {!loading && !error && results.length === 0 && query && (
        <p className="no-results">No results found. Try different search terms.</p>
      )}
    </div>
  )
}

export default IngredientSearch
