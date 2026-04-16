import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { searchByUpload } from '../services/api'

function ImageUpload({ onSearchSuccess }) {
  const [preview, setPreview] = useState(null)
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const [topK, setTopK] = useState(5)
  const [weights, setWeights] = useState({ color: 0.7, texture: 0.2, shape: 0.1 })

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length === 0) return
    const selected = acceptedFiles[0]
    setFile(selected)
    setPreview(URL.createObjectURL(selected))
    setError(null)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/png': ['.png'], 'image/jpeg': ['.jpg', '.jpeg'] },
    maxFiles: 1,
    maxSize: 16 * 1024 * 1024,
  })

  const handleSearch = async () => {
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      const data = await searchByUpload({ file, topK, weights })
      onSearchSuccess({ searchResponse: data, queryPreview: preview })
    } catch (err) {
      setError(err.response?.data?.error || 'Search failed. Is the backend running?')
    } finally {
      setUploading(false)
    }
  }

  const handleReset = () => {
    setFile(null)
    setPreview(null)
    setError(null)
  }

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors
          ${isDragActive ? 'border-green-500 bg-green-50' : 'border-gray-300 hover:border-green-400 hover:bg-gray-50'}`}
      >
        <input {...getInputProps()} />
        {preview ? (
          <div className="space-y-3">
            <img src={preview} alt="Preview" className="mx-auto max-h-64 rounded-lg shadow" />
            <p className="text-sm text-gray-500">{file.name}</p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="text-4xl">📁</div>
            <p className="text-gray-600 font-medium">
              {isDragActive ? 'Drop your fruit image here...' : 'Drag & drop a fruit image here'}
            </p>
            <p className="text-sm text-gray-400">or click to select (PNG, JPG — max 16MB)</p>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 px-4 py-2 rounded-lg text-sm">{error}</div>
      )}

      {file && (
        <div className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label className="text-sm text-gray-600">
              Top K
              <input
                type="number"
                min={1}
                max={20}
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value || 5))}
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              />
            </label>
            <div className="grid grid-cols-3 gap-2">
              <label className="text-xs text-gray-600">
                Color
                <input
                  type="number"
                  step="0.1"
                  min={0}
                  max={1}
                  value={weights.color}
                  onChange={(e) => setWeights((prev) => ({ ...prev, color: Number(e.target.value || 0) }))}
                  className="mt-1 w-full rounded-md border border-gray-300 px-2 py-2 text-sm"
                />
              </label>
              <label className="text-xs text-gray-600">
                Texture
                <input
                  type="number"
                  step="0.1"
                  min={0}
                  max={1}
                  value={weights.texture}
                  onChange={(e) => setWeights((prev) => ({ ...prev, texture: Number(e.target.value || 0) }))}
                  className="mt-1 w-full rounded-md border border-gray-300 px-2 py-2 text-sm"
                />
              </label>
              <label className="text-xs text-gray-600">
                Shape
                <input
                  type="number"
                  step="0.1"
                  min={0}
                  max={1}
                  value={weights.shape}
                  onChange={(e) => setWeights((prev) => ({ ...prev, shape: Number(e.target.value || 0) }))}
                  className="mt-1 w-full rounded-md border border-gray-300 px-2 py-2 text-sm"
                />
              </label>
            </div>
          </div>
          <div className="flex gap-3 justify-center">
          <button
            onClick={handleSearch}
            disabled={uploading}
            className="bg-green-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {uploading ? 'Searching...' : 'Search Similar Fruits'}
          </button>
          <button
            onClick={handleReset}
            className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Clear
          </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default ImageUpload
