// 统一请求封装：基于 fetch，零外部依赖
// 后端 FastAPI 需实现 /api 前缀下的接口，返回 JSON

const BASE_URL = '/api'

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export class HttpError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
  }
}

export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = localStorage.getItem('token')

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })

  // 401 未登录或 token 失效 → 回到登录页
  if (res.status === 401) {
    localStorage.removeItem('token')
    if (location.pathname !== '/login') location.href = '/login'
    throw new HttpError(401, '登录已过期')
  }

  if (!res.ok) {
    throw new HttpError(res.status, `请求失败（${res.status}）`)
  }

  const body: ApiResponse<T> = await res.json()
  if (body.code !== 0) {
    throw new Error(body.message || '请求失败')
  }
  return body.data
}

export const get = <T>(path: string) => request<T>(path)

export const post = <T>(path: string, data?: unknown) =>
  request<T>(path, { method: 'POST', body: data ? JSON.stringify(data) : undefined })

export const put = <T>(path: string, data?: unknown) =>
  request<T>(path, { method: 'PUT', body: data ? JSON.stringify(data) : undefined })

export const del = <T>(path: string) => request<T>(path, { method: 'DELETE' })
