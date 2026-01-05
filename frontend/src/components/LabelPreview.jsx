import React, { useState, useEffect } from 'react'
import { generateLabel } from '../api/client'

function LabelPreview({ perServing, productName, ingredientsList, allergens, onLabelGenerated, labelData, onStartOver, onBack }) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!labelData) {
      generateLabelImage()
    }
  }, [])

  const generateLabelImage = async () => {
    setIsGenerating(true)
    setError(null)

    try {
      const data = await generateLabel(perServing, productName, ingredientsList, allergens)
      onLabelGenerated(data)
    } catch (err) {
      setError(err.message || 'Failed to generate label')
    } finally {
      setIsGenerating(false)
    }
  }

  const downloadPNG = () => {
    if (!labelData?.imageBase64) return

    const link = document.createElement('a')
    link.href = `data:image/png;base64,${labelData.imageBase64}`
    link.download = `nutrition-label${productName ? `-${productName.replace(/[^a-z0-9]/gi, '-')}` : ''}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const downloadPDF = () => {
    if (!labelData?.pdfBase64) return

    const link = document.createElement('a')
    link.href = `data:application/pdf;base64,${labelData.pdfBase64}`
    link.download = `nutrition-label${productName ? `-${productName.replace(/[^a-z0-9]/gi, '-')}` : ''}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="label-preview">
      <h2>Your Nutrition Label</h2>

      {isGenerating && (
        <div className="generating-label">
          <div className="spinner" />
          <p>Generating your label...</p>
        </div>
      )}

      {error && (
        <div className="label-error">
          <p>{error}</p>
          <button onClick={generateLabelImage} className="btn-secondary">
            Try Again
          </button>
        </div>
      )}

      {labelData && (
        <div className="label-content">
          <div className="label-image-container">
            <img
              src={`data:image/png;base64,${labelData.imageBase64}`}
              alt="Nutrition Facts Label"
              className="label-image"
            />
          </div>

          <div className="label-actions">
            <h3>Download Label</h3>
            <div className="download-buttons">
              <button onClick={downloadPNG} className="btn-primary">
                Download PNG
              </button>
              <button onClick={downloadPDF} className="btn-primary">
                Download PDF
              </button>
            </div>
          </div>

          <div className="label-info">
            {ingredientsList && (
              <div className="info-section">
                <h4>Ingredients</h4>
                <p>{ingredientsList}</p>
              </div>
            )}

            {allergens && allergens.length > 0 && (
              <div className="info-section">
                <h4>Contains</h4>
                <p>{allergens.join(', ')}</p>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="preview-actions">
        <button onClick={onBack} className="btn-secondary">
          Back to Serving Size
        </button>
        <button onClick={onStartOver} className="btn-secondary">
          Start New Product
        </button>
      </div>
    </div>
  )
}

export default LabelPreview
