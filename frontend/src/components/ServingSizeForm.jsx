import React, { useState } from 'react'
import { calculatePerServing } from '../api/client'

function ServingSizeForm({ nutrition, onConfirm, onBack }) {
  const [servingSizeG, setServingSizeG] = useState(30)
  const [servingDescription, setServingDescription] = useState('1 serving (30g)')
  const [servingsPerContainer, setServingsPerContainer] = useState(1)
  const [isCalculating, setIsCalculating] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    // Validate inputs
    if (servingSizeG <= 0) {
      setError('Serving size must be greater than 0')
      return
    }
    if (servingsPerContainer <= 0) {
      setError('Servings per container must be greater than 0')
      return
    }
    if (!servingDescription.trim()) {
      setError('Please enter a serving description')
      return
    }

    setIsCalculating(true)

    try {
      const servingConfig = {
        serving_size_g: servingSizeG,
        serving_size_description: servingDescription,
        servings_per_container: servingsPerContainer
      }

      const perServing = await calculatePerServing(nutrition, servingConfig)
      onConfirm(servingConfig, perServing)
    } catch (err) {
      setError(err.message || 'Calculation failed')
    } finally {
      setIsCalculating(false)
    }
  }

  const updateDescription = (grams) => {
    setServingSizeG(grams)
    setServingDescription(`1 serving (${grams}g)`)
  }

  return (
    <div className="serving-size-form">
      <h2>Configure Serving Size</h2>
      <p className="form-description">
        Enter the serving size information for your nutrition label.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="servingSize">Serving Size (grams)</label>
          <input
            type="number"
            id="servingSize"
            value={servingSizeG}
            onChange={(e) => updateDescription(parseFloat(e.target.value) || 0)}
            min="0.1"
            step="0.1"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="servingDescription">Serving Description</label>
          <input
            type="text"
            id="servingDescription"
            value={servingDescription}
            onChange={(e) => setServingDescription(e.target.value)}
            placeholder="e.g., 1 cookie (30g), 2 tbsp (28g)"
            required
          />
          <p className="form-hint">
            This appears on the label (e.g., "1 cookie (30g)", "2 tbsp (28g)")
          </p>
        </div>

        <div className="form-group">
          <label htmlFor="servingsPerContainer">Servings Per Container</label>
          <input
            type="number"
            id="servingsPerContainer"
            value={servingsPerContainer}
            onChange={(e) => setServingsPerContainer(parseFloat(e.target.value) || 0)}
            min="0.1"
            step="0.1"
            required
          />
        </div>

        {error && (
          <div className="form-error">
            {error}
          </div>
        )}

        <div className="form-actions">
          <button type="button" onClick={onBack} className="btn-secondary">
            Back to Edit
          </button>
          <button type="submit" className="btn-primary" disabled={isCalculating}>
            {isCalculating ? 'Calculating...' : 'Generate Label'}
          </button>
        </div>
      </form>

      <div className="serving-examples">
        <h4>Common Serving Sizes</h4>
        <div className="example-buttons">
          <button type="button" onClick={() => { setServingSizeG(28); setServingDescription('2 tbsp (28g)') }}>
            2 tbsp (28g)
          </button>
          <button type="button" onClick={() => { setServingSizeG(30); setServingDescription('1 serving (30g)') }}>
            30g serving
          </button>
          <button type="button" onClick={() => { setServingSizeG(50); setServingDescription('1 piece (50g)') }}>
            50g piece
          </button>
          <button type="button" onClick={() => { setServingSizeG(100); setServingDescription('100g') }}>
            100g
          </button>
        </div>
      </div>
    </div>
  )
}

export default ServingSizeForm
