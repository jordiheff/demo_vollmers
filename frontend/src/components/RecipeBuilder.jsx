import React, { useState, useMemo, useEffect, useCallback } from 'react'
import IngredientSearch from './IngredientSearch'
import { combineIngredients, convertIngredientToGrams, getSupportedUnits } from '../api/client'

const NUTRITION_FIELDS = [
  { key: 'calories', label: 'Calories', unit: '' },
  { key: 'total_fat_g', label: 'Total Fat', unit: 'g' },
  { key: 'saturated_fat_g', label: 'Saturated Fat', unit: 'g' },
  { key: 'trans_fat_g', label: 'Trans Fat', unit: 'g' },
  { key: 'cholesterol_mg', label: 'Cholesterol', unit: 'mg' },
  { key: 'sodium_mg', label: 'Sodium', unit: 'mg' },
  { key: 'total_carbohydrate_g', label: 'Total Carbs', unit: 'g' },
  { key: 'dietary_fiber_g', label: 'Dietary Fiber', unit: 'g' },
  { key: 'total_sugars_g', label: 'Total Sugars', unit: 'g' },
  { key: 'added_sugars_g', label: 'Added Sugars', unit: 'g' },
  { key: 'protein_g', label: 'Protein', unit: 'g' },
  { key: 'vitamin_d_mcg', label: 'Vitamin D', unit: 'mcg' },
  { key: 'calcium_mg', label: 'Calcium', unit: 'mg' },
  { key: 'iron_mg', label: 'Iron', unit: 'mg' },
  { key: 'potassium_mg', label: 'Potassium', unit: 'mg' },
]

// Default units to show if API call fails
const DEFAULT_UNITS = {
  weight_units: [
    { value: 'g', label: 'Gram' },
    { value: 'kg', label: 'Kilogram' },
    { value: 'oz', label: 'Ounce' },
    { value: 'lb', label: 'Pound' },
  ],
  volume_units: [
    { value: 'cup', label: 'Cup' },
    { value: 'tbsp', label: 'Tablespoon' },
    { value: 'tsp', label: 'Teaspoon' },
    { value: 'ml', label: 'Milliliter' },
    { value: 'fl_oz', label: 'Fluid Ounce' },
  ],
  count_units: [
    { value: 'whole', label: 'Whole' },
    { value: 'large', label: 'Large' },
    { value: 'medium', label: 'Medium' },
    { value: 'small', label: 'Small' },
    { value: 'stick', label: 'Stick' },
    { value: 'packet', label: 'Packet' },
  ],
}

function RecipeBuilder({ onRecipeComplete, onBack }) {
  const [ingredients, setIngredients] = useState([])
  const [recipeName, setRecipeName] = useState('')
  const [showSearch, setShowSearch] = useState(true)
  const [availableUnits, setAvailableUnits] = useState(DEFAULT_UNITS)
  const [convertingIds, setConvertingIds] = useState(new Set())

  // Load available units on mount
  useEffect(() => {
    getSupportedUnits()
      .then(setAvailableUnits)
      .catch((err) => {
        console.warn('Failed to load units, using defaults:', err)
      })
  }, [])

  // Flatten units for the dropdown
  const allUnits = useMemo(() => {
    const units = []

    // Weight units first (most common for direct entry)
    units.push({ group: 'Weight', items: availableUnits.weight_units || [] })
    units.push({ group: 'Volume', items: availableUnits.volume_units || [] })
    units.push({ group: 'Count', items: availableUnits.count_units || [] })

    return units
  }, [availableUnits])

  // Convert ingredient to grams when quantity or unit changes
  // Returns { grams, confidence, note }
  const convertIngredient = useCallback(async (ingredient) => {
    // Skip if already in grams
    if (ingredient.unit === 'g') {
      return { grams: ingredient.quantity, confidence: 'high', note: null }
    }

    setConvertingIds((prev) => new Set(prev).add(ingredient.id))

    try {
      const result = await convertIngredientToGrams(
        ingredient.description,
        ingredient.quantity,
        ingredient.unit
      )
      return {
        grams: result.grams,
        confidence: result.confidence,
        note: result.note
      }
    } catch (err) {
      console.error('Conversion failed:', err)
      // Return estimate based on quantity if conversion fails
      return {
        grams: ingredient.quantity * 100,
        confidence: 'low',
        note: 'Conversion failed. Using rough estimate.'
      }
    } finally {
      setConvertingIds((prev) => {
        const next = new Set(prev)
        next.delete(ingredient.id)
        return next
      })
    }
  }, [])

  const handleAddIngredient = (ingredient) => {
    const newIngredient = {
      ...ingredient,
      quantity: 100,
      unit: 'g',
      weight_g: 100, // default weight in grams
      confidence: 'high', // grams are always high confidence
      conversionNote: null,
      id: Date.now(), // unique key for list
    }
    setIngredients((prev) => [...prev, newIngredient])
  }

  const handleRemoveIngredient = (id) => {
    setIngredients((prev) => prev.filter((ing) => ing.id !== id))
  }

  const handleQuantityChange = async (id, quantity) => {
    const parsedQuantity = parseFloat(quantity) || 0

    setIngredients((prev) =>
      prev.map((ing) => {
        if (ing.id !== id) return ing

        // If unit is grams, weight_g equals quantity directly
        if (ing.unit === 'g') {
          return {
            ...ing,
            quantity: parsedQuantity,
            weight_g: parsedQuantity,
            confidence: 'high',
            conversionNote: null
          }
        }

        // Otherwise, mark as needs conversion
        return { ...ing, quantity: parsedQuantity, weight_g: null, confidence: null }
      })
    )

    // Trigger conversion for non-gram units
    const ingredient = ingredients.find((ing) => ing.id === id)
    if (ingredient && ingredient.unit !== 'g') {
      const result = await convertIngredient({ ...ingredient, quantity: parsedQuantity })
      setIngredients((prev) =>
        prev.map((ing) =>
          ing.id === id
            ? { ...ing, weight_g: result.grams, confidence: result.confidence, conversionNote: result.note }
            : ing
        )
      )
    }
  }

  const handleUnitChange = async (id, unit) => {
    // First update the unit
    setIngredients((prev) =>
      prev.map((ing) => {
        if (ing.id !== id) return ing

        // If changing to grams, weight_g equals quantity directly
        if (unit === 'g') {
          return {
            ...ing,
            unit,
            weight_g: ing.quantity,
            confidence: 'high',
            conversionNote: null
          }
        }

        // Otherwise, mark as needs conversion
        return { ...ing, unit, weight_g: null, confidence: null }
      })
    )

    // Trigger conversion for non-gram units
    const ingredient = ingredients.find((ing) => ing.id === id)
    if (ingredient && unit !== 'g') {
      const result = await convertIngredient({ ...ingredient, unit })
      setIngredients((prev) =>
        prev.map((ing) =>
          ing.id === id
            ? { ...ing, weight_g: result.grams, confidence: result.confidence, conversionNote: result.note }
            : ing
        )
      )
    }
  }

  // Legacy handler for direct gram input (still used internally)
  const handleWeightChange = (id, weight) => {
    setIngredients((prev) =>
      prev.map((ing) =>
        ing.id === id
          ? { ...ing, weight_g: parseFloat(weight) || 0, confidence: 'high', conversionNote: null }
          : ing
      )
    )
  }

  const totalWeight = useMemo(() => {
    return ingredients.reduce((sum, ing) => sum + (ing.weight_g || 0), 0)
  }, [ingredients])

  const combinedNutrition = useMemo(() => {
    // Only calculate if all ingredients have weight_g
    const allConverted = ingredients.every((ing) => ing.weight_g != null && ing.weight_g > 0)
    if (ingredients.length === 0 || !allConverted) return null
    return combineIngredients(ingredients)
  }, [ingredients])

  // Check if any ingredients have low/medium confidence
  const hasLowConfidence = ingredients.some((ing) => ing.confidence === 'low')
  const hasMediumConfidence = ingredients.some((ing) => ing.confidence === 'medium')
  const hasWarnings = hasLowConfidence || hasMediumConfidence

  const handleConfirm = () => {
    if (!combinedNutrition || ingredients.length === 0) return

    onRecipeComplete({
      product_name: recipeName || 'Recipe',
      nutrition: combinedNutrition,
      ingredients: ingredients.map((ing) => ({
        description: ing.description,
        quantity: ing.quantity,
        unit: ing.unit,
        weight_g: ing.weight_g,
        fdc_id: ing.fdc_id,
      })),
      total_weight_g: totalWeight,
    })
  }

  const formatValue = (value) => {
    if (value == null) return '-'
    return value < 10 ? value.toFixed(1) : Math.round(value)
  }

  const formatWeight = (weight) => {
    if (weight == null) return '...'
    return weight < 10 ? weight.toFixed(1) : Math.round(weight)
  }

  const getConfidenceIcon = (confidence) => {
    if (confidence === 'high') return null
    if (confidence === 'medium') return '~'
    if (confidence === 'low') return '!'
    return null
  }

  const getConfidenceClass = (confidence) => {
    if (confidence === 'high') return ''
    if (confidence === 'medium') return 'confidence-medium'
    if (confidence === 'low') return 'confidence-low'
    return ''
  }

  const isConverting = convertingIds.size > 0
  const hasIncompleteConversions = ingredients.some((ing) => ing.weight_g == null)

  return (
    <div className="recipe-builder">
      <div className="recipe-header">
        <h2>Recipe Builder</h2>
        <p>Search and add ingredients to calculate combined nutrition</p>
      </div>

      <div className="recipe-name-input">
        <label htmlFor="recipe-name">Recipe Name</label>
        <input
          id="recipe-name"
          type="text"
          value={recipeName}
          onChange={(e) => setRecipeName(e.target.value)}
          placeholder="Enter recipe name"
        />
      </div>

      <div className="recipe-content">
        <div className="ingredients-section">
          <div className="section-header">
            <h3>Ingredients ({ingredients.length})</h3>
            <button
              onClick={() => setShowSearch(!showSearch)}
              className="toggle-search"
            >
              {showSearch ? 'Hide Search' : 'Add Ingredient'}
            </button>
          </div>

          {showSearch && (
            <IngredientSearch onIngredientSelect={handleAddIngredient} />
          )}

          {ingredients.length > 0 ? (
            <div className="ingredients-list">
              <table className="ingredients-table">
                <thead>
                  <tr>
                    <th>Ingredient</th>
                    <th>Amount</th>
                    <th>Unit</th>
                    <th>= Grams</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {ingredients.map((ing) => (
                    <tr
                      key={ing.id}
                      className={`${convertingIds.has(ing.id) ? 'converting' : ''} ${getConfidenceClass(ing.confidence)}`}
                    >
                      <td className="ingredient-name">
                        <span className="name">{ing.description}</span>
                        <span className="meta">{ing.data_type}</span>
                      </td>
                      <td className="ingredient-quantity">
                        <input
                          type="number"
                          value={ing.quantity}
                          onChange={(e) => handleQuantityChange(ing.id, e.target.value)}
                          min="0"
                          step="0.1"
                          className="quantity-input"
                        />
                      </td>
                      <td className="ingredient-unit">
                        <select
                          value={ing.unit}
                          onChange={(e) => handleUnitChange(ing.id, e.target.value)}
                          className="unit-select"
                        >
                          {allUnits.map((group) => (
                            <optgroup key={group.group} label={group.group}>
                              {group.items.map((unit) => (
                                <option key={unit.value} value={unit.value}>
                                  {unit.label}
                                </option>
                              ))}
                            </optgroup>
                          ))}
                        </select>
                      </td>
                      <td className="ingredient-grams">
                        {convertingIds.has(ing.id) ? (
                          <span className="converting-indicator">...</span>
                        ) : (
                          <span
                            className={`grams-value ${getConfidenceClass(ing.confidence)}`}
                            title={ing.conversionNote || ''}
                          >
                            {getConfidenceIcon(ing.confidence) && (
                              <span className="confidence-icon">{getConfidenceIcon(ing.confidence)}</span>
                            )}
                            {formatWeight(ing.weight_g)}g
                          </span>
                        )}
                      </td>
                      <td className="ingredient-actions">
                        <button
                          onClick={() => handleRemoveIngredient(ing.id)}
                          className="remove-button"
                          title="Remove ingredient"
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td colSpan="3"><strong>Total</strong></td>
                    <td>
                      <strong>
                        {hasIncompleteConversions ? '...' : `${formatWeight(totalWeight)}g`}
                      </strong>
                    </td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>

              {/* Confidence Warning Banner */}
              {hasWarnings && !hasIncompleteConversions && (
                <div className={`confidence-warning ${hasLowConfidence ? 'warning-low' : 'warning-medium'}`}>
                  <span className="warning-icon">{hasLowConfidence ? '!' : '~'}</span>
                  <span className="warning-text">
                    {hasLowConfidence
                      ? 'Some weights are estimates and may not be accurate. Consider entering weights in grams for better accuracy.'
                      : 'Some weights are approximations. Hover over values with ~ for details.'}
                  </span>
                </div>
              )}
            </div>
          ) : (
            <p className="no-ingredients">No ingredients added yet. Use the search above to find and add ingredients.</p>
          )}
        </div>

        <div className="nutrition-preview">
          <h3>Combined Nutrition (per 100g)</h3>
          {combinedNutrition ? (
            <table className="nutrition-table">
              <thead>
                <tr>
                  <th>Nutrient</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody>
                {NUTRITION_FIELDS.map((field) => (
                  <tr key={field.key}>
                    <td>{field.label}</td>
                    <td>
                      {formatValue(combinedNutrition[field.key])}{field.unit}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="no-nutrition">
              {hasIncompleteConversions
                ? 'Converting measurements...'
                : 'Add ingredients to see combined nutrition'}
            </p>
          )}
        </div>
      </div>

      <div className="recipe-actions">
        <button onClick={onBack} className="btn-secondary">
          Back
        </button>
        <button
          onClick={handleConfirm}
          disabled={!combinedNutrition || ingredients.length === 0 || isConverting}
          className="btn-primary"
        >
          {isConverting ? 'Converting...' : 'Use This Nutrition Data'}
        </button>
      </div>
    </div>
  )
}

export default RecipeBuilder
