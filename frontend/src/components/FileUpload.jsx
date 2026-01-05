import React, { useState, useCallback } from 'react'
import { extractNutrition, extractRecipeFromFile } from '../api/client'

function FileUpload({ onExtraction, onError, mode = 'specsheet' }) {
  const [isDragging, setIsDragging] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [fileName, setFileName] = useState(null)

  const isRecipeMode = mode === 'recipe'

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    const files = e.dataTransfer.files
    if (files.length > 0) {
      handleFile(files[0])
    }
  }, [])

  const handleFileInput = useCallback((e) => {
    const files = e.target.files
    if (files.length > 0) {
      handleFile(files[0])
    }
  }, [])

  const handleFile = async (file) => {
    // Validate file type
    const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/gif', 'text/plain']
    const isValid = validTypes.some(type => file.type.startsWith(type.split('/')[0]) || file.type === type)

    if (!isValid && !file.name.endsWith('.pdf')) {
      onError('Please upload a PDF, image, or text file')
      return
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      onError('File size must be less than 10MB')
      return
    }

    setFileName(file.name)
    setIsLoading(true)

    try {
      if (isRecipeMode) {
        // Extract recipe from file
        const data = await extractRecipeFromFile(file)
        onExtraction(data)
      } else {
        // Extract nutrition from spec sheet
        const data = await extractNutrition(file)
        onExtraction(data)
      }
    } catch (err) {
      onError(err.message || `Failed to extract ${isRecipeMode ? 'recipe' : 'nutrition'} data`)
    } finally {
      setIsLoading(false)
    }
  }

  const loadingMessage = isRecipeMode
    ? `Extracting recipe from ${fileName}...`
    : `Extracting nutrition data from ${fileName}...`

  const dropMessage = isRecipeMode
    ? 'Drop your recipe here'
    : 'Drop your spec sheet here'

  return (
    <div className="file-upload-container">
      <div
        className={`file-upload-zone ${isDragging ? 'dragging' : ''} ${isLoading ? 'loading' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {isLoading ? (
          <div className="upload-loading">
            <div className="spinner" />
            <p>{loadingMessage}</p>
            <p className="loading-note">This may take a moment</p>
          </div>
        ) : (
          <>
            <div className="upload-icon">{isRecipeMode ? '🍳' : '📄'}</div>
            <h4>{dropMessage}</h4>
            <p>or click to browse</p>
            <p className="supported-formats">Supported: PDF, PNG, JPG</p>
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.gif,.txt"
              onChange={handleFileInput}
              className="file-input"
            />
          </>
        )}
      </div>
    </div>
  )
}

export default FileUpload
