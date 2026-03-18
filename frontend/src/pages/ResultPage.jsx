import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { searchSimilar, getImage } from '../services/api'
import ResultGrid from '../components/ResultGrid'
import FeatureCharts from '../components/FeatureCharts'

function ResultPage() {
  const { imageId } = useParams()
  const [queryImage, setQueryImage] = useState(null)
  const [results, setResults] = useState([])
  const [queryTime, setQueryTime] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function fetchResults() {
      setLoading(true)
      setError(null)
      try {
        const [imageData, searchData] = await Promise.all([
          getImage(imageId),
          searchSimilar(imageId),
        ])
        setQueryImage(imageData)
        setResults(searchData.results)
        setQueryTime(searchData.query_time_ms)
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to fetch results. Is the backend running?')
      } finally {
        setLoading(false)
      }
    }
    fetchResults()
  }, [imageId])

  if (loading) {
    return (
      <div className="text-center py-20">
        <div className="inline-block w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-4 text-gray-500">Searching for similar images...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-20 space-y-4">
        <p className="text-red-600">{error}</p>
        <Link to="/" className="text-green-600 hover:underline">Back to Home</Link>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <Link to="/" className="text-green-600 hover:underline text-sm">&larr; New Search</Link>
        {queryTime !== null && (
          <span className="text-sm text-gray-400">Query time: {queryTime}ms</span>
        )}
      </div>

      {queryImage && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Query Image</h2>
          <div className="flex items-center gap-6">
            <img
              src={queryImage.image_url}
              alt="Query"
              className="w-40 h-40 object-cover rounded-lg shadow"
            />
            <div className="space-y-1 text-sm text-gray-600">
              <p><span className="font-medium">Label:</span> {queryImage.fruit_label}</p>
              <p><span className="font-medium">Size:</span> {queryImage.width} x {queryImage.height}</p>
              <p><span className="font-medium">File:</span> {queryImage.filename}</p>
            </div>
          </div>
        </div>
      )}

      <ResultGrid results={results} queryImage={queryImage} />

      <FeatureCharts results={results} />
    </div>
  )
}

export default ResultPage
