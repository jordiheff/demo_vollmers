import React, { useState, useEffect } from 'react'
import { calculateRecipeNutrition } from '../api/client'

function RecipeReview({ recipeData, onConfirm, onBack, onError }) {
  const [recipe, setRecipe] = useState(recipeData.recipe)
  const [nutritionResult, setNutritionResult] = useState(recipeData.nutritionResult)
  const [yieldWeight, setYieldWeight] = useState(
    recipeData.nutritionResult?.yield_weight_g || recipeData.nutritionResult?.total_raw_weight_g || 0
  )
  const [isRecalculating, setIsRecalculating] = useState(false)
  const [showExtractedText, setShowExtractedText] = useState(false)

  const ingredients = nutritionResult?.ingredients || []
  const flags = nutritionResult?.flags || []
  const nutritionPer100g = nutritionResult?.nutrition_per_100g || {}

  const handleYieldWeightChange = (e) => {
    const value = parseFloat(e.target.value) || 0
    setYieldWeight(value)
  }

  const handleRecalculate = async () => {
    setIsRecalculating(true)
    try {
      const result = await calculateRecipeNutrition(recipe, {
        yieldWeightG: yieldWeight
      })
      setNutritionResult(result)
    } catch (err) {
      onError(err.message || 'Failed to recalculate nutrition')
    } finally {
      setIsRecalculating(false)
    }
  }

  const handleConfirm = () => {
    onConfirm({
      recipe_name: recipe.name,
      ingredients: nutritionResult.ingredients,
      nutrition_per_100g: nutritionResult.nutrition_per_100g,
      total_weight_g: nutritionResult.total_raw_weight_g,
      yield_weight_g: nutritionResult.yield_weight_g
    })
  }

  const getConfidenceBadge = (confidence) => {
    const colors = {
      high: 'badge-success',
      medium: 'badge-warning',
      low: 'badge-error'
    }
    return colors[confidence] || 'badge-default'
  }

  const formatNumber = (num, decimals = 1) => {
    if (num === null || num === undefined) return '-'
    return Number(num).toFixed(decimals)
  }

  return (
    <div className="recipe-review">
      <div className="review-header">
        <h2>{recipe.name || 'Recipe Review'}</h2>
        <p className="review-subtitle">
          Review the extracted ingredients and calculated nutrition below.
        </p>
      </div>

      {/* Flags/Warnings */}
      {flags.length > 0 && (
        <div className="flags-section">
          <h3>Notices</h3>
          <div className="flags-list">
            {flags.map((flag, index) => (
              <div key={index} className={`flag flag-${flag.severity}`}>
                <span className="flag-icon">
                  {flag.severity === 'error' ? '!' : flag.severity === 'warning' ? '!' : 'i'}
                </span>
                <span className="flag-message">{flag.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Ingredients Table */}
      <div className="ingredients-section">
        <h3>Parsed Ingredients ({ingredients.length})</h3>
        <div className="ingredients-table-wrapper">
          <table className="ingredients-table">
            <thead>
              <tr>
                <th>Ingredient</th>
                <th>Original</th>
                <th>Quantity</th>
                <th>Grams</th>
                <th>Source</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {ingredients.map((ing, index) => (
                <tr key={index} className={ing.conversion_confidence === 'low' ? 'row-warning' : ''}>
                  <td>
                    <strong>{ing.name_normalized || ing.name}</strong>
                    {ing.name_normalized && ing.name_normalized !== ing.name && (
                      <span className="original-name"> ({ing.name})</span>
                    )}
                  </td>
                  <td className="text-muted">{ing.raw_text}</td>
                  <td>{formatNumber(ing.quantity, 2)} {ing.unit}</td>
                  <td>
                    <strong>{formatNumber(ing.grams, 1)}g</strong>
                  </td>
                  <td>
                    <span className={`source-badge source-${ing.conversion_source}`}>
                      {ing.conversion_source === 'table' ? 'Table' :
                       ing.conversion_source === 'direct' ? 'Direct' :
                       ing.conversion_source === 'usda' ? 'USDA' :
                       ing.conversion_source === 'estimate' ? 'Est.' : ing.conversion_source}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${getConfidenceBadge(ing.conversion_confidence)}`}>
                      {ing.conversion_confidence}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan="3"><strong>Total Raw Weight</strong></td>
                <td colSpan="3"><strong>{formatNumber(nutritionResult?.total_raw_weight_g, 1)}g</strong></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Yield Weight */}
      <div className="yield-section">
        <h3>Final Product Weight</h3>
        <p className="section-description">
          Adjust if your recipe has water loss during cooking (e.g., baked goods weigh less than raw ingredients).
        </p>
        <div className="yield-input-group">
          <label>
            Final Weight (g):
            <input
              type="number"
              value={yieldWeight}
              onChange={handleYieldWeightChange}
              min="1"
              step="1"
            />
          </label>
          <button
            onClick={handleRecalculate}
            disabled={isRecalculating}
            className="btn-secondary"
          >
            {isRecalculating ? 'Recalculating...' : 'Recalculate'}
          </button>
        </div>
        {recipe.yield_description && (
          <p className="yield-description">Yield: {recipe.yield_description}</p>
        )}
      </div>

      {/* Nutrition Preview */}
      <div className="nutrition-preview-section">
        <h3>Calculated Nutrition (per 100g)</h3>
        <div className="nutrition-grid">
          <div className="nutrition-item">
            <span className="nutrition-label">Calories</span>
            <span className="nutrition-value">{formatNumber(nutritionPer100g.calories, 0)}</span>
          </div>
          <div className="nutrition-item">
            <span className="nutrition-label">Total Fat</span>
            <span className="nutrition-value">{formatNumber(nutritionPer100g.total_fat_g)}g</span>
          </div>
          <div className="nutrition-item">
            <span className="nutrition-label">Saturated Fat</span>
            <span className="nutrition-value">{formatNumber(nutritionPer100g.saturated_fat_g)}g</span>
          </div>
          <div className="nutrition-item">
            <span className="nutrition-label">Cholesterol</span>
            <span className="nutrition-value">{formatNumber(nutritionPer100g.cholesterol_mg)}mg</span>
          </div>
          <div className="nutrition-item">
            <span className="nutrition-label">Sodium</span>
            <span className="nutrition-value">{formatNumber(nutritionPer100g.sodium_mg)}mg</span>
          </div>
          <div className="nutrition-item">
            <span className="nutrition-label">Total Carbs</span>
            <span className="nutrition-value">{formatNumber(nutritionPer100g.total_carbohydrate_g)}g</span>
          </div>
          <div className="nutrition-item">
            <span className="nutrition-label">Dietary Fiber</span>
            <span className="nutrition-value">{formatNumber(nutritionPer100g.dietary_fiber_g)}g</span>
          </div>
          <div className="nutrition-item">
            <span className="nutrition-label">Total Sugars</span>
            <span className="nutrition-value">{formatNumber(nutritionPer100g.total_sugars_g)}g</span>
          </div>
          <div className="nutrition-item">
            <span className="nutrition-label">Protein</span>
            <span className="nutrition-value">{formatNumber(nutritionPer100g.protein_g)}g</span>
          </div>
        </div>
      </div>

      {/* Extracted Text (collapsible) */}
      <div className="extracted-text-section">
        <button
          onClick={() => setShowExtractedText(!showExtractedText)}
          className="btn-link"
        >
          {showExtractedText ? 'Hide' : 'Show'} Extracted Text
        </button>
        {showExtractedText && (
          <pre className="extracted-text">{recipeData.extractedText}</pre>
        )}
      </div>

      {/* Actions */}
      <div className="review-actions">
        <button onClick={onBack} className="btn-secondary">
          Back
        </button>
        <button onClick={handleConfirm} className="btn-primary">
          Continue to Review Nutrition
        </button>
      </div>
    </div>
  )
}

export default RecipeReview
