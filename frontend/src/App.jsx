import { Routes, Route, Link } from 'react-router-dom'
import HomePage from './pages/HomePage'
import ResultPage from './pages/ResultPage'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold text-green-700 hover:text-green-800">
            Fruit CBIR System
          </Link>
          <span className="text-sm text-gray-500">Content-Based Image Retrieval</span>
        </div>
      </nav>
      <main className="max-w-6xl mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/result/:imageId" element={<ResultPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
