import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

export async function searchByUpload({ file, topK = 5, weights = { color: 0.7, texture: 0.2, shape: 0.1 } }) {
  const formData = new FormData()
  formData.append('image', file)
  formData.append('top_k', String(topK))
  formData.append('weight_color', String(weights.color))
  formData.append('weight_texture', String(weights.texture))
  formData.append('weight_shape', String(weights.shape))

  const res = await api.post('/search', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function getFruits() {
  const res = await api.get('/fruits')
  return res.data
}
