import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

const DEFAULT_WEIGHTS = {
  color: 0.10,
  color_moments: 0.00,
  texture: 0.20,
  glcm: 0.70,
  shape: 0.00,
}

export async function searchByUpload({ file, topK = 5, weights = DEFAULT_WEIGHTS }) {
  const formData = new FormData()
  formData.append('image', file)
  formData.append('top_k', String(topK))
  formData.append('weight_color', String(weights.color))
  formData.append('weight_color_moments', String(weights.color_moments))
  formData.append('weight_texture', String(weights.texture))
  formData.append('weight_glcm', String(weights.glcm))
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
