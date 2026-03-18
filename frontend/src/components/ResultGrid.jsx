function ResultGrid({ results, queryImage }) {
  if (!results || results.length === 0) {
    return <p className="text-gray-500 text-center">No results found.</p>
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-800">Top-5 Similar Images</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
        {results.map((result, index) => (
          <div
            key={result.image_id}
            className={`bg-white rounded-xl shadow-sm border overflow-hidden transition-transform hover:scale-105
              ${index === 0 ? 'ring-2 ring-green-500' : 'border-gray-200'}`}
          >
            <div className="aspect-square bg-gray-100 flex items-center justify-center">
              <img
                src={result.image_url}
                alt={result.fruit_label}
                className="w-full h-full object-cover"
                onError={(e) => { e.target.src = '' ; e.target.alt = 'Image not found' }}
              />
            </div>
            <div className="p-3 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-green-700">#{index + 1}</span>
                <span className="text-xs font-semibold text-blue-600">
                  {(result.similarity * 100).toFixed(1)}%
                </span>
              </div>
              <p className="text-sm font-medium text-gray-800 truncate">{result.fruit_label}</p>
              <p className="text-xs text-gray-400">Distance: {result.distance.toFixed(3)}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ResultGrid
