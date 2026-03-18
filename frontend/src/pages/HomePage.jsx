import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ImageUpload from '../components/ImageUpload'
import { getStats } from '../services/api'

function HomePage() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch(() => setStats(null))
  }, [])

  const handleUploadSuccess = (data) => {
    navigate(`/result/${data.image_id}`)
  }

  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">Fruit Image Search</h1>
        <p className="text-gray-500">Upload a fruit image to find the 5 most similar images in our database</p>
      </div>

      <div className="max-w-xl mx-auto">
        <ImageUpload onUploadSuccess={handleUploadSuccess} />
      </div>

      {stats && stats.total_images > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Database Statistics</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-green-700">{stats.total_images.toLocaleString()}</p>
              <p className="text-sm text-gray-500">Total Images</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">{stats.categories?.length || 0}</p>
              <p className="text-sm text-gray-500">Categories</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">{stats.total_features.toLocaleString()}</p>
              <p className="text-sm text-gray-500">Features Extracted</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-orange-600">{stats.total_queries}</p>
              <p className="text-sm text-gray-500">Queries Made</p>
            </div>
          </div>
          {stats.categories && stats.categories.length > 0 && (
            <div className="flex flex-wrap gap-2 justify-center">
              {stats.categories.map((cat) => (
                <span
                  key={cat.fruit_label}
                  className="bg-green-50 text-green-700 text-sm px-3 py-1 rounded-full border border-green-200"
                >
                  {cat.fruit_label} ({cat.count})
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default HomePage
