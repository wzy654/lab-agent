// ============================================================
// 统一请求封装：基于 axios
// 作用：全项目所有接口请求都走这一个文件，统一做三件事：
//   1. 自动拼接后端地址（BASE_URL）
//   2. 自动在请求头携带登录 token
//   3. 统一处理错误（token 过期跳登录、弹出后端错误信息）
// 后端 FastAPI 统一返回 { code, message, data } 三段式 JSON
// 约定：code === 200 表示业务成功（后端 app/exceptions.py 的 ErrorCode.OK）
// ============================================================

// axios 是第三方 HTTP 请求库（npm install axios 安装）
// AxiosError 是 axios 的错误类型，用于标注 catch 回调里 err 参数的类型
import axios, { AxiosError } from 'axios'
// 从同目录的 auth.ts 导入 token 和用户信息的清除方法（见 utils/auth.ts）
import { getToken, removeToken, removeUserInfo } from './auth'

// import.meta.env.VITE_API_BASE：读取项目根目录 .env 文件里的配置项
// （Vite 要求环境变量必须以 VITE_ 开头才会暴露给前端代码）
// || '/api' 是兜底写法：如果 .env 里没配置，就用 '/api'
const BASE_URL = import.meta.env.VITE_API_BASE || '/api'

// 静态文件（上传的图片等）的基础地址：把 API 地址末尾的 /api 去掉
// 例：http://127.0.0.1:8000/api → http://127.0.0.1:8000
const FILE_BASE = BASE_URL.replace(/\/api$/, '')

// 把后端返回的相对路径（如 uploads/xxx.png）拼成可直接访问的完整 URL
// 已经是完整地址（http 开头）的原样返回
export function fileUrl(url: string) {
  return url.startsWith('http') ? url : `${FILE_BASE}/${url}`
}

// 创建一个 axios 实例。不直接用全局 axios，是为了让配置只影响本项目
const instance = axios.create({
  baseURL: BASE_URL, // 所有请求的 URL 都会自动拼上这个前缀
  timeout: 30000, // 30秒超时：请求超过 30 秒没响应就报错
})

// TypeScript 泛型接口：描述后端响应体的固定结构
// <T> 是泛型占位符，代表 data 字段的实际类型，调用时才确定
// 例如 get<UserInfo[]>('/users') 表示 data 是 UserInfo 数组
export interface ApiResponse<T> {
  code: number // 业务状态码：200 成功，400/401/500 等为失败
  message: string // 提示信息（成功或失败的原因）
  data: T // 后端返回的具体数据
}

// 自定义的 HTTP 错误类，继承自 JS 内置的 Error
// 用于区分「HTTP 层错误」（404、500 等）和普通业务错误
export class HttpError extends Error {
  constructor(
    public status: number, // public 简写：自动创建 this.status 属性
    message: string, // 传给父类 Error 的错误信息
  ) {
    super(message) // 调用父类构造函数，把错误信息交给 Error
  }
}

// ============ 请求拦截器 ============
// 拦截器：每个请求发出前都会经过这里，相当于「发请求前的统一预处理」
instance.interceptors.request.use((config) => {
  const token = getToken() // 从 localStorage 读取登录时保存的 token
  if (token) {
    // 已登录就在请求头加上 Authorization 字段
    // Bearer 是后端 JWT 认证的固定格式：Bearer + 空格 + token
    config.headers.Authorization = `Bearer ${token}`
  }
  return config // 必须返回配置，请求才会继续发出
})

// ============ 响应拦截器 ============
// 每个响应回来后先经过这里，再做业务处理，相当于「收响应后的统一后处理」
// 有两个回调：第一个处理「HTTP 成功」，第二个处理「HTTP 报错（4xx/5xx/断网）」
instance.interceptors.response.use(
  (res) => {
    // res 是 axios 的响应对象，res.data 才是后端返回的 JSON 内容
    const body = res.data as ApiResponse<unknown> // as：类型断言，告诉 TS 这就是响应体结构
    // 后端约定 code === 200 表示成功（见 app/exceptions.py ErrorCode.OK）
    if (body.code !== 200) {
      // 业务失败（如「账号不存在」）：抛出普通 Error，信息用后端给的 message
      // Promise.reject：把正常流程转为失败流程，调用方的 await 会抛出异常进入 catch
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    // 业务成功：不返回整个 body，只返回 data 部分
    // 这样调用方拿到的直接就是数据本身，不用每次都写 body.data
    return body.data as never
  },
  (err: AxiosError<ApiResponse<unknown>>) => {
    // err.response 是 HTTP 层的响应（可能不存在，比如断网时）
    // ?. 可选链：如果前面是 null/undefined 就不继续取值，避免报错
    const status = err.response?.status // HTTP 状态码，如 404、500
    // 401 = 未登录或 token 已失效 → 清掉本地登录状态，强制回登录页
    if (status === 401) {
      removeToken()      // 清 token：路由守卫靠它判断「未登录」，不清会死循环
      removeUserInfo()   // 清用户信息：避免残留上一个账号的数据
      // location.href 是整页跳转（会重新加载整个应用），
      // 内存里的全局状态也会随之重新初始化，不会有残留
      // pathname 是当前路径（如 /users）：已经在登录页就不用再跳，避免死循环
      if (location.pathname !== '/login') location.href = '/login'
      return Promise.reject(new HttpError(401, '登录已过期，请重新登录'))
    }
    // 其他错误：优先显示后端返回的具体错误信息（如「账号不存在」）
    // ?? 空值合并：左边为 null/undefined 时才用右边的值
    const msg = err.response?.data?.message || `请求失败（${status ?? '网络异常'}）`
    return Promise.reject(new HttpError(status ?? 0, msg))
  },
)

// ============ 对外暴露的请求方法 ============
// request<T>：通用方法。path 是接口路径（如 '/auth/login'），会自动拼上 BASE_URL
// <T> 泛型：调用时传入期望的返回数据类型，如 request<LoginResult>(...)
// options?.method 中的 ?. 表示 options 可能是 undefined
// ?? 'GET' 表示不传 method 时默认用 GET
export function request<T>(
  path: string,
  options?: {
    method?: string
    data?: unknown
    // GET 的查询参数：axios 会拼到 URL 上（如 /user/list?page=1&username=admin）
    // 注意：GET 的参数放这里（URL 上），POST/PUT 的才放 data（请求体里）
    params?: Record<string, unknown>
  },
) {
  // instance.request<never, T> 的第二个泛型参数 T 表示「拦截器处理完之后的返回类型」
  // （拦截器已经把 body.data 剥出来了，所以返回值就是 T）
  return instance.request<never, T>({
    url: path,
    method: options?.method ?? 'GET',
    data: options?.data, // POST/PUT 的请求体，axios 会自动 JSON 序列化
    params: options?.params, // GET 的查询参数，axios 会自动拼 URL 并做 URL 编码
  })
}

// 下面几个是快捷方法，日常开发直接用它们即可
// get：查询数据，params 是查询参数（可选）
export const get = <T>(path: string, params?: Record<string, unknown>) =>
  request<T>(path, { params })

// post：新建数据，data 是要提交的内容
export const post = <T>(path: string, data?: unknown) =>
  request<T>(path, { method: 'POST', data })

// put：更新数据
export const put = <T>(path: string, data?: unknown) => request<T>(path, { method: 'PUT', data })

// del：删除数据（不叫 delete 是为了避免和 JS 保留字混淆）
export const del = <T>(path: string) => request<T>(path, { method: 'DELETE' })

// upload：上传文件专用。和 post 的区别是请求体用 FormData（multipart/form-data 格式），
// 而不是 JSON——后端 UploadFile 参数只认 multipart 表单
// new FormData() 是浏览器内置对象，append(字段名, 文件) 把文件装进表单；
// 字段名必须是 'file'，和后端 upload(file: UploadFile) 的参数名一致
// 注意：不能手动设 Content-Type，axios 检测到 FormData 会自动加上
// multipart 边界（boundary），手动设反而会缺 boundary 导致后端解析失败
export async function upload<T>(path: string, file: File) {
  const fd = new FormData()
  fd.append('file', file)
  return instance.request<never, T>({ url: path, method: 'POST', data: fd })
}
