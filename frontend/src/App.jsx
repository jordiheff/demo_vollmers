import React, { useState } from 'react'
import FileUpload from './components/FileUpload'
import NutritionEditor from './components/NutritionEditor'
import ServingSizeForm from './components/ServingSizeForm'
import LabelPreview from './components/LabelPreview'
import RecipeBuilder from './components/RecipeBuilder'
import RecipeReview from './components/RecipeReview'

const STEPS = {
  UPLOAD: 'upload',
  RECIPE: 'recipe',
  RECIPE_REVIEW: 'recipe_review',
  EDIT: 'edit',
  SERVING: 'serving',
  PREVIEW: 'preview'
}

function App() {
  const [step, setStep] = useState(STEPS.UPLOAD)
  const [extractedData, setExtractedData] = useState(null)
  const [nutrition, setNutrition] = useState(null)
  const [servingConfig, setServingConfig] = useState(null)
  const [perServing, setPerServing] = useState(null)
  const [labelData, setLabelData] = useState(null)
  const [error, setError] = useState(null)
  const [recipeData, setRecipeData] = useState(null) // For recipe extraction

  const handleExtraction = (data) => {
    setExtractedData(data)
    setNutrition(data.nutrition)
    setError(null)
    setStep(STEPS.EDIT)
  }

  // Handle recipe extracted from image/PDF
  const handleRecipeExtraction = (data) => {
    setRecipeData(data)
    setError(null)
    setStep(STEPS.RECIPE_REVIEW)
  }

  // Handle recipe review complete - move to nutrition editor
  const handleRecipeReviewComplete = (reviewedData) => {
    const ingredientsList = reviewedData.ingredients
      .map((ing) => ing.name_normalized || ing.name)
      .join(', ')

    setExtractedData({
      product_name: reviewedData.recipe_name,
      nutrition: reviewedData.nutrition_per_100g,
      ingredients_list: ingredientsList,
      allergens: [],
    })
    setNutrition(reviewedData.nutrition_per_100g)
    setError(null)
    setStep(STEPS.EDIT)
  }

  const handleRecipeComplete = (recipeData) => {
    setExtractedData({
      product_name: recipeData.product_name,
      nutrition: recipeData.nutrition,
      ingredients_list: recipeData.ingredients.map((i) => i.description).join(', '),
      allergens: [],
    })
    setNutrition(recipeData.nutrition)
    setError(null)
    setStep(STEPS.EDIT)
  }

  const handleBuildRecipe = () => {
    setStep(STEPS.RECIPE)
  }

  const handleNutritionConfirm = (updatedNutrition) => {
    setNutrition(updatedNutrition)
    setStep(STEPS.SERVING)
  }

  const handleServingConfirm = async (config, perServingData) => {
    setServingConfig(config)
    setPerServing(perServingData)
    setStep(STEPS.PREVIEW)
  }

  const handleLabelGenerated = (data) => {
    setLabelData(data)
  }

  const handleStartOver = () => {
    setStep(STEPS.UPLOAD)
    setExtractedData(null)
    setNutrition(null)
    setServingConfig(null)
    setPerServing(null)
    setLabelData(null)
    setError(null)
    setRecipeData(null)
  }

  const handleBack = () => {
    if (step === STEPS.EDIT) {
      setStep(STEPS.UPLOAD)
    } else if (step === STEPS.RECIPE) {
      setStep(STEPS.UPLOAD)
    } else if (step === STEPS.RECIPE_REVIEW) {
      setStep(STEPS.UPLOAD)
    } else if (step === STEPS.SERVING) {
      setStep(STEPS.EDIT)
    } else if (step === STEPS.PREVIEW) {
      setStep(STEPS.SERVING)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Nutrition Label Generator</h1>
        <p className="subtitle">Create FDA-compliant nutrition labels from spec sheets</p>
      </header>

      <main className="app-main">
        {/* Progress indicator */}
        <div className="progress-bar">
          <div className={`progress-step ${step === STEPS.UPLOAD ? 'active' : step !== STEPS.UPLOAD ? 'completed' : ''}`}>
            <span className="step-number">1</span>
            <span className="step-label">Upload</span>
          </div>
          <div className="progress-line" />
          <div className={`progress-step ${step === STEPS.EDIT ? 'active' : [STEPS.SERVING, STEPS.PREVIEW].includes(step) ? 'completed' : ''}`}>
            <span className="step-number">2</span>
            <span className="step-label">Review</span>
          </div>
          <div className="progress-line" />
          <div className={`progress-step ${step === STEPS.SERVING ? 'active' : step === STEPS.PREVIEW ? 'completed' : ''}`}>
            <span className="step-number">3</span>
            <span className="step-label">Serving</span>
          </div>
          <div className="progress-line" />
          <div className={`progress-step ${step === STEPS.PREVIEW ? 'active' : ''}`}>
            <span className="step-number">4</span>
            <span className="step-label">Label</span>
          </div>
        </div>

        {error && (
          <div className="error-banner">
            {error}
            <button onClick={() => setError(null)} className="error-dismiss">×</button>
          </div>
        )}

        {/* Step content */}
        <div className="step-content">
          {step === STEPS.UPLOAD && (
            <div className="upload-options">
              <div className="upload-section">
                <h3>Upload Spec Sheet</h3>
                <p>Upload a nutrition spec sheet with per-100g values</p>
                <FileUpload
                  onExtraction={handleExtraction}
                  onError={setError}
                  mode="specsheet"
                />
              </div>
              <div className="option-divider">
                <span>or</span>
              </div>
              <div className="upload-section">
                <h3>Upload Recipe</h3>
                <p>Upload a recipe image or PDF to extract ingredients and calculate nutrition</p>
                <FileUpload
                  onExtraction={handleRecipeExtraction}
                  onError={setError}
                  mode="recipe"
                />
              </div>
              <div className="option-divider">
                <span>or</span>
              </div>
              <div className="recipe-option">
                <h3>Build from USDA</h3>
                <p>Search the USDA database and combine ingredients manually.</p>
                <button onClick={handleBuildRecipe} className="btn-secondary">
                  Build Recipe
                </button>
              </div>
            </div>
          )}

          {step === STEPS.RECIPE && (
            <RecipeBuilder
              onRecipeComplete={handleRecipeComplete}
              onBack={handleBack}
            />
          )}

          {step === STEPS.RECIPE_REVIEW && recipeData && (
            <RecipeReview
              recipeData={recipeData}
              onConfirm={handleRecipeReviewComplete}
              onBack={handleBack}
              onError={setError}
            />
          )}

          {step === STEPS.EDIT && extractedData && (
            <NutritionEditor
              extractedData={extractedData}
              nutrition={nutrition}
              onConfirm={handleNutritionConfirm}
              onBack={handleBack}
            />
          )}

          {step === STEPS.SERVING && nutrition && (
            <ServingSizeForm
              nutrition={nutrition}
              onConfirm={handleServingConfirm}
              onBack={handleBack}
            />
          )}

          {step === STEPS.PREVIEW && perServing && (
            <LabelPreview
              perServing={perServing}
              productName={extractedData?.product_name}
              ingredientsList={extractedData?.ingredients_list}
              allergens={extractedData?.allergens || []}
              onLabelGenerated={handleLabelGenerated}
              labelData={labelData}
              onStartOver={handleStartOver}
              onBack={handleBack}
            />
          )}
        </div>
      </main>

      <footer className="app-footer">
        <p>Creates FDA 2020 compliant nutrition labels</p>
      </footer>
    </div>
  )
}

export default App
