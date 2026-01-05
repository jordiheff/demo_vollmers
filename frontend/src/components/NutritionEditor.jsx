import React, { useState } from 'react'
import FlagBadge from './FlagBadge'

const NUTRIENT_CONFIG = [
  { key: 'calories', label: 'Calories', unit: '' },
  { key: 'total_fat_g', label: 'Total Fat', unit: 'g' },
  { key: 'saturated_fat_g', label: 'Saturated Fat', unit: 'g', indent: true },
  { key: 'trans_fat_g', label: 'Trans Fat', unit: 'g', indent: true },
  { key: 'cholesterol_mg', label: 'Cholesterol', unit: 'mg' },
  { key: 'sodium_mg', label: 'Sodium', unit: 'mg' },
  { key: 'total_carbohydrate_g', label: 'Total Carbohydrate', unit: 'g' },
  { key: 'dietary_fiber_g', label: 'Dietary Fiber', unit: 'g', indent: true },
  { key: 'total_sugars_g', label: 'Total Sugars', unit: 'g', indent: true },
  { key: 'added_sugars_g', label: 'Added Sugars', unit: 'g', indent: true },
  { key: 'protein_g', label: 'Protein', unit: 'g' },
  { key: 'vitamin_d_mcg', label: 'Vitamin D', unit: 'mcg' },
  { key: 'calcium_mg', label: 'Calcium', unit: 'mg' },
  { key: 'iron_mg', label: 'Iron', unit: 'mg' },
  { key: 'potassium_mg', label: 'Potassium', unit: 'mg' },
]

function NutritionEditor({ extractedData, nutrition, onConfirm, onBack }) {
  const [values, setValues] = useState({ ...nutrition })
  const [editingField, setEditingField] = useState(null)

  const handleChange = (key, value) => {
    const numValue = value === '' ? null : parseFloat(value)
    setValues(prev => ({
      ...prev,
      [key]: isNaN(numValue) ? null : numValue
    }))
  }

  const getFlagsForField = (fieldKey) => {
    return (extractedData.flags || []).filter(f => f.field === fieldKey)
  }

  const handleConfirm = () => {
    onConfirm(values)
  }

  return (
    <div className="nutrition-editor">
      <div className="editor-header">
        <h2>Review Extracted Nutrition Data</h2>
        {extractedData.product_name && (
          <p className="product-name">Product: {extractedData.product_name}</p>
        )}
        {extractedData.product_code && (
          <p className="product-code">Code: {extractedData.product_code}</p>
        )}
      </div>

      <div className="nutrition-table">
        <div className="table-header">
          <span>Nutrient</span>
          <span>Per 100g</span>
          <span>Flags</span>
        </div>

        {NUTRIENT_CONFIG.map(({ key, label, unit, indent }) => {
          const flags = getFlagsForField(key)
          const value = values[key]

          return (
            <div
              key={key}
              className={`nutrient-row ${indent ? 'indented' : ''} ${flags.length > 0 ? 'has-flags' : ''}`}
            >
              <span className="nutrient-label">{label}</span>
              <span className="nutrient-value">
                <input
                  type="number"
                  step="0.1"
                  value={value === null ? '' : value}
                  onChange={(e) => handleChange(key, e.target.value)}
                  onFocus={() => setEditingField(key)}
                  onBlur={() => setEditingField(null)}
                  className={editingField === key ? 'editing' : ''}
                  placeholder="—"
                />
                <span className="unit">{unit}</span>
              </span>
              <span className="nutrient-flags">
                {flags.map((flag, i) => (
                  <FlagBadge key={i} flag={flag} />
                ))}
              </span>
            </div>
          )
        })}
      </div>

      {extractedData.ingredients_list && (
        <div className="ingredients-section">
          <h3>Ingredients</h3>
          <p>{extractedData.ingredients_list}</p>
        </div>
      )}

      {extractedData.allergens && extractedData.allergens.length > 0 && (
        <div className="allergens-section">
          <h3>Allergens</h3>
          <div className="allergen-tags">
            {extractedData.allergens.map((allergen, i) => (
              <span key={i} className="allergen-tag">{allergen}</span>
            ))}
          </div>
        </div>
      )}

      <div className="editor-actions">
        <button onClick={onBack} className="btn-secondary">
          Back
        </button>
        <button onClick={handleConfirm} className="btn-primary">
          Continue to Serving Size
        </button>
      </div>
    </div>
  )
}

export default NutritionEditor
