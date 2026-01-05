/**
 * API client for Nutrition Label Generator backend
 */

const API_BASE = '/api'

/**
 * Extract nutrition data from an uploaded file
 * @param {File} file - The file to extract from
 * @returns {Promise<object>} Extracted product data
 */
export async function extractNutrition(file) {
  // Convert file to base64
  const base64 = await fileToBase64(file)

  // Determine file type
  const fileType = detectFileType(file.name)

  const response = await fetch(`${API_BASE}/extract`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      file_content: base64,
      file_type: fileType,
      filename: file.name,
    }),
  })

  const data = await response.json()

  if (!data.success) {
    throw new Error(data.error || 'Extraction failed')
  }

  return data.product
}

/**
 * Calculate per-serving nutrition values
 * @param {object} nutrition - Nutrition per 100g
 * @param {object} servingConfig - Serving configuration
 * @returns {Promise<object>} Per-serving nutrition with %DV
 */
export async function calculatePerServing(nutrition, servingConfig) {
  const response = await fetch(`${API_BASE}/calculate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      nutrition,
      serving_config: servingConfig,
    }),
  })

  const data = await response.json()

  if (!data.success) {
    throw new Error(data.error || 'Calculation failed')
  }

  return data.per_serving
}

/**
 * Generate nutrition label
 * @param {object} perServing - Per-serving nutrition data
 * @param {string} productName - Optional product name
 * @param {string} ingredientsList - Optional ingredients list
 * @param {string[]} allergens - Optional allergens array
 * @returns {Promise<object>} Label images in base64
 */
export async function generateLabel(perServing, productName, ingredientsList, allergens) {
  const response = await fetch(`${API_BASE}/label`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      per_serving: perServing,
      product_name: productName,
      ingredients_list: ingredientsList,
      allergens: allergens || [],
    }),
  })

  const data = await response.json()

  if (!data.success) {
    throw new Error(data.error || 'Label generation failed')
  }

  return {
    imageBase64: data.image_base64,
    pdfBase64: data.pdf_base64,
  }
}

/**
 * Convert a File to base64 string
 * @param {File} file
 * @returns {Promise<string>}
 */
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      // Remove the data URL prefix
      const base64 = reader.result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

/**
 * Detect file type from filename
 * @param {string} filename
 * @returns {string}
 */
function detectFileType(filename) {
  const lower = filename.toLowerCase()
  if (lower.endsWith('.pdf')) return 'pdf'
  if (lower.match(/\.(png|jpg|jpeg|gif|bmp|tiff|webp)$/)) return 'image'
  return 'text'
}

// ----- Recipe API Functions -----

/**
 * Extract and parse a recipe from an uploaded file
 * @param {File} file - The recipe image or PDF
 * @returns {Promise<object>} Parsed recipe with nutrition
 */
export async function extractRecipeFromFile(file) {
  // Convert file to base64
  const base64 = await fileToBase64(file)

  // Determine file type
  const fileType = detectFileType(file.name)

  const response = await fetch(`${API_BASE}/recipe/extract-from-file`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      file_content: base64,
      file_type: fileType,
      filename: file.name,
    }),
  })

  const data = await response.json()

  if (!data.success) {
    throw new Error(data.error || 'Recipe extraction failed')
  }

  return {
    recipe: data.recipe,
    nutritionResult: data.nutrition_result,
    extractedText: data.extracted_text,
  }
}

/**
 * Calculate nutrition for a recipe
 * @param {object} recipe - Recipe with ingredients
 * @param {object} options - Options including ingredient USDA IDs and yield weight
 * @returns {Promise<object>} Calculated nutrition
 */
export async function calculateRecipeNutrition(recipe, options = {}) {
  const response = await fetch(`${API_BASE}/recipe/calculate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      recipe,
      ingredient_usda_ids: options.ingredientUsdaIds,
      yield_weight_g: options.yieldWeightG,
    }),
  })

  const data = await response.json()

  if (!data.success) {
    throw new Error(data.error || 'Recipe calculation failed')
  }

  return data.result
}

/**
 * Get list of supported ingredients for volume conversion
 * @returns {Promise<object[]>} List of supported ingredients
 */
export async function getSupportedIngredients() {
  const response = await fetch(`${API_BASE}/recipe/ingredients`)
  const data = await response.json()
  return data.ingredients
}

/**
 * Convert an ingredient measurement to grams
 * @param {string} ingredient - Ingredient name
 * @param {number} quantity - Numeric amount
 * @param {string} unit - Unit of measurement (cup, tbsp, tsp, g, oz, etc.)
 * @returns {Promise<object>} Conversion result with grams and confidence
 */
export async function convertIngredientToGrams(ingredient, quantity, unit) {
  const response = await fetch(`${API_BASE}/recipe/convert`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ingredient,
      quantity,
      unit,
    }),
  })

  const data = await response.json()

  if (!data.success) {
    throw new Error(data.error || 'Conversion failed')
  }

  return data.result
}

/**
 * Get list of supported measurement units
 * @returns {Promise<object>} Object with volume_units, weight_units, count_units
 */
export async function getSupportedUnits() {
  const response = await fetch(`${API_BASE}/recipe/units`)
  return response.json()
}

// ----- USDA API Functions -----

/**
 * Search for foods in the USDA FoodData Central database
 * @param {string} query - Search term
 * @param {object} options - Search options
 * @param {string[]} options.dataTypes - Filter by data type
 * @param {number} options.pageSize - Results per page
 * @returns {Promise<object>} Search results
 */
export async function searchUSDAFoods(query, options = {}) {
  const params = new URLSearchParams({ q: query })

  if (options.dataTypes && options.dataTypes.length) {
    params.set('data_types', options.dataTypes.join(','))
  }
  if (options.pageSize) {
    params.set('page_size', options.pageSize.toString())
  }

  const response = await fetch(`${API_BASE}/usda/search?${params}`)
  const data = await response.json()

  if (!data.success) {
    throw new Error(data.error || 'USDA search failed')
  }

  return data.results
}

/**
 * Get nutrition data for a specific USDA food
 * @param {number} fdcId - FoodData Central ID
 * @returns {Promise<object>} Nutrition data per 100g
 */
export async function getUSDAFoodNutrition(fdcId) {
  const response = await fetch(`${API_BASE}/usda/food/${fdcId}`)
  const data = await response.json()

  if (!data.success) {
    throw new Error(data.error || 'Failed to fetch USDA food')
  }

  return {
    description: data.description,
    nutrition: data.nutrition,
  }
}

/**
 * Get USDA cache statistics
 * @returns {Promise<object>} Cache stats
 */
export async function getUSDACacheStats() {
  const response = await fetch(`${API_BASE}/usda/cache/stats`)
  return response.json()
}

/**
 * Combine multiple ingredients into aggregate nutrition
 * @param {Array<{nutrition: object, weight_g: number}>} ingredients
 * @returns {object} Combined nutrition per 100g
 */
export function combineIngredients(ingredients) {
  const totalWeight = ingredients.reduce((sum, ing) => sum + ing.weight_g, 0)

  if (totalWeight === 0) {
    return null
  }

  const combined = {
    calories: 0,
    total_fat_g: 0,
    saturated_fat_g: 0,
    trans_fat_g: 0,
    cholesterol_mg: 0,
    sodium_mg: 0,
    total_carbohydrate_g: 0,
    dietary_fiber_g: 0,
    total_sugars_g: 0,
    added_sugars_g: 0,
    protein_g: 0,
    vitamin_d_mcg: 0,
    calcium_mg: 0,
    iron_mg: 0,
    potassium_mg: 0,
  }

  // Sum weighted values
  for (const ing of ingredients) {
    const factor = ing.weight_g / 100 // nutrition is per 100g
    for (const key of Object.keys(combined)) {
      if (ing.nutrition[key] != null) {
        combined[key] += ing.nutrition[key] * factor
      }
    }
  }

  // Convert back to per 100g
  const per100gFactor = 100 / totalWeight
  for (const key of Object.keys(combined)) {
    combined[key] = combined[key] * per100gFactor
  }

  return combined
}
