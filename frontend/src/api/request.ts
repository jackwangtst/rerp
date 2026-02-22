import axios from 'axios'
import { useAuthStore } from '@/store/auth'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
})

// 请求拦截：自动附加 JWT Token
request.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

// 响应拦截：统一错误处理
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const message = error.response?.data?.detail || error.message

    if (status === 401) {
      useAuthStore().logout()
      window.location.href = '/login'
    } else {
      ElMessage.error(message || '请求失败')
    }
    return Promise.reject(error)
  },
)

export default request
