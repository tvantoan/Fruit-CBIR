import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ImageUpload from '../components/ImageUpload'
import { getFruits } from '../services/api'

function HomePage() {
  const navigate = useNavigate()
  const [fruits, setFruits] = useState([])

  useEffect(() => {
    getFruits()
      .then((data) => setFruits(data.fruits || []))
      .catch(() => setFruits([]))
  }, [])

  const handleSearchSuccess = ({ searchResponse, queryPreview }) => {
    navigate('/result', {
      state: {
        searchResponse,
        queryPreview,
      },
    })
  }

  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">Fruit Image Search</h1>
        <p className="text-gray-500">Upload a fruit image to find similar images in our database</p>
      </div>

      <div className="max-w-xl mx-auto">
        <ImageUpload onSearchSuccess={handleSearchSuccess} />
      </div>

      {fruits.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Available Fruits</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {fruits.map((fruit) => (
              <div key={fruit.fruit_id} className="rounded-lg border border-gray-200 overflow-hidden bg-gray-50">
                <div className="aspect-square bg-gray-100 flex items-center justify-center">
                  {fruit.sample_image_url ? (
                    <img
                      src={fruit.sample_image_url}
                      alt={fruit.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <span className="text-xs text-gray-400">No image</span>
                  )}
                </div>
                <div className="p-2 text-center">
                  <p className="text-sm font-medium text-gray-800 truncate">{fruit.name}</p>
                </div>
              </div>
            ))}
            </div>
        </div>
      )}
    </div>
  )
}

export default HomePage
