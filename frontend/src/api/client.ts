import axios from 'axios'

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error)) {
      const msg: string =
        (error.response?.data as { detail?: string } | undefined)?.detail ??
        error.message ??
        '请求失败'
      return Promise.reject(new Error(msg))
    }
    return Promise.reject(error)
  },
)

export default client
