import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { uploadImage } from '../services/api'

function ImageUpload({ onUploadSuccess }) {
  const [preview, setPreview] = useState(null)
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)

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

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      const data = await uploadImage(file)
      onUploadSuccess(data)
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed. Is the backend running?')
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
        <div className="flex gap-3 justify-center">
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="bg-green-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {uploading ? 'Uploading...' : 'Search Similar Fruits'}
          </button>
          <button
            onClick={handleReset}
            className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Clear
          </button>
        </div>
      )}
    </div>
  )
}

export default ImageUpload
