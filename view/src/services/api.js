import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})


export async function searchByUpload({ file, topK = 5 }) {
  const formData = new FormData()
  formData.append('image', file)

  const res = await api.post('/search', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function getFruits() {
  const res = await api.get('/fruits')
  return res.data
}

export async function getOptimizationStatus() {
  const res = await api.get('/admin/optimize')
  return res.data
}

export async function startOptimization({ nTrials = 100 } = {}) {
  const res = await api.post('/admin/optimize', { n_trials: nTrials })
  return res.data
}

export async function evaluateFeatures({ subsetSize = 100 } = {}) {
  const res = await api.get('/admin/evaluate-features', { params: { subset_size: subsetSize } })
  return res.data
}

export async function evaluateTestDataset({ sampleSize = 50, topK = 5 } = {}) {
  const res = await api.get('/admin/test-evaluation', {
    params: { sample_size: sampleSize, top_k: topK },
  })
  return res.data
}
