import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

function FeatureCharts({ results }) {
  if (!results || results.length === 0) return null

  const distanceData = {
    labels: results.map((_, i) => `#${i + 1}`),
    datasets: [
      {
        label: 'Color Distance',
        data: results.map(r => r.feature_distances?.color ?? 0),
        backgroundColor: 'rgba(239, 68, 68, 0.7)',
      },
      {
        label: 'Texture Distance',
        data: results.map(r => r.feature_distances?.texture ?? 0),
        backgroundColor: 'rgba(59, 130, 246, 0.7)',
      },
      {
        label: 'Shape Distance',
        data: results.map(r => r.feature_distances?.shape ?? 0),
        backgroundColor: 'rgba(16, 185, 129, 0.7)',
      },
    ],
  }

  const distanceOptions = {
    responsive: true,
    plugins: {
      title: { display: true, text: 'Feature Distance Breakdown per Result' },
      legend: { position: 'top' },
    },
    scales: {
      y: { beginAtZero: true, title: { display: true, text: 'Distance' } },
    },
  }

  const similarityData = {
    labels: results.map((r, i) => `#${i + 1} ${r.fruit_label}`),
    datasets: [
      {
        label: 'Similarity %',
        data: results.map(r => (r.similarity * 100).toFixed(1)),
        backgroundColor: results.map((_, i) =>
          i === 0 ? 'rgba(16, 185, 129, 0.8)' : 'rgba(59, 130, 246, 0.6)'
        ),
      },
    ],
  }

  const similarityOptions = {
    indexAxis: 'y',
    responsive: true,
    plugins: {
      title: { display: true, text: 'Similarity Score (%)' },
      legend: { display: false },
    },
    scales: {
      x: { beginAtZero: true, max: 100 },
    },
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-800">Analysis</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <Bar data={similarityData} options={similarityOptions} />
        </div>
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
          <Bar data={distanceData} options={distanceOptions} />
        </div>
      </div>
    </div>
  )
}

export default FeatureCharts
