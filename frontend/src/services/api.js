import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

export async function uploadImage(file) {
  const formData = new FormData()
  formData.append('image', file)
  const res = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function searchSimilar(imageId) {
  const res = await api.get(`/search?image_id=${imageId}`)
  return res.data
}

export async function getImage(imageId) {
  const res = await api.get(`/images/${imageId}`)
  return res.data
}

export async function getStats() {
  const res = await api.get('/stats')
  return res.data
}
