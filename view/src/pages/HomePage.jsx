import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import ImageUpload from '../components/ImageUpload'
import { getFruits } from '../services/api'

function HomePage() {
  const navigate = useNavigate()
  const [fruits, setFruits] = useState([])
  const [sampleUrl, setSampleUrl] = useState(null)
  const sampleCounter = useRef(0)

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

  const handleSampleClick = (fruit) => {
    if (!fruit.sample_image_url) return
    // Append a counter so the same URL clicked twice still re-triggers the effect.
    sampleCounter.current += 1
    setSampleUrl(`${fruit.sample_image_url}?t=${sampleCounter.current}`)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">Fruit Image Search</h1>
        <p className="text-gray-500">Upload a fruit image, or click a sample below to use it as the query</p>
      </div>

      <div className="max-w-xl mx-auto">
        <ImageUpload onSearchSuccess={handleSearchSuccess} querySampleUrl={sampleUrl} />
      </div>

      {fruits.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Available Fruits — click to use as query</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {fruits.map((fruit) => (
              <button
                key={fruit.fruit_id}
                type="button"
                onClick={() => handleSampleClick(fruit)}
                className="text-left rounded-lg border border-gray-200 overflow-hidden bg-gray-50 cursor-pointer hover:border-green-400 hover:shadow-md transition-all"
              >
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
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default HomePage
