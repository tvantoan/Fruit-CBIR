import { Link, useLocation } from 'react-router-dom'
import ResultGrid from '../components/ResultGrid'
import FeatureCharts from '../components/FeatureCharts'

function ResultPage() {
  const { state } = useLocation()
  const searchResponse = state?.searchResponse
  const queryPreview = state?.queryPreview

  if (!searchResponse) {
    return (
      <div className="text-center py-20 space-y-4">
        <p className="text-red-600">No search result data found. Please start a new search.</p>
        <Link to="/" className="text-green-600 hover:underline">Back to Home</Link>
      </div>
    )
  }

  const results = Array.isArray(searchResponse.results) ? searchResponse.results : []
  const queryTime = searchResponse.query_stats?.query_time_ms ?? null

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <Link to="/" className="text-green-600 hover:underline text-sm">&larr; New Search</Link>
        {queryTime !== null && (
          <span className="text-sm text-gray-400">Query time: {queryTime}ms</span>
        )}
      </div>

      {queryPreview && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Uploaded Query Image</h2>
          <div className="flex items-center gap-6">
            <img
              src={queryPreview}
              alt="Query"
              className="w-40 h-40 object-cover rounded-lg shadow"
            />
            <div className="space-y-1 text-sm text-gray-600">
              <p><span className="font-medium">Top K:</span> {searchResponse.query_stats?.top_k ?? '-'}</p>
              <p className="font-medium">Weights:</p>
              <ul className="grid grid-cols-2 gap-x-4 text-xs text-gray-500 ml-2">
                <li>Color: {searchResponse.query_stats?.weights_applied?.color ?? '-'}</li>
                <li>C.Moments: {searchResponse.query_stats?.weights_applied?.color_moments ?? '-'}</li>
                <li>Texture (LBP): {searchResponse.query_stats?.weights_applied?.texture ?? '-'}</li>
                <li>GLCM: {searchResponse.query_stats?.weights_applied?.glcm ?? '-'}</li>
                <li>Shape: {searchResponse.query_stats?.weights_applied?.shape ?? '-'}</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      <ResultGrid results={results} />

      <FeatureCharts results={results} />
    </div>
  )
}

export default ResultPage
