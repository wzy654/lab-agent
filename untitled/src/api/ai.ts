// AI 对话模块
// 后端已实现：
//   POST /api/ai/chat         { messages: ChatMessage[] } → data 为回复字符串（一次性）
//   POST /api/ai/chat/stream  { messages: ChatMessage[] } → SSE 流（逐帧推事件）
// （后端 service 返回 Result.success(回复文本)，没有 {reply} 这层包装）

import { post } from '@/utils/request'
import { getToken } from '@/utils/auth'
import type { ChatMessage } from './types'

// 流式事件类型：与后端 agent_service.stream_agent 的事件一一对应
export type StreamEvent =
  | { type: 'status'; message: string } // 开始思考
  | { type: 'tool_start'; name: string; message: string } // 工具开始（message 已是中文文案）
  | { type: 'tool_end'; name: string; message: string } // 工具结束
  | { type: 'token'; content: string } // 回答文本的增量片段
  | { type: 'done' } // 全部完成
  | { type: 'error'; message: string } // 出错

export const aiApi = {
  async chat(messages: ChatMessage[]): Promise<string> {
    // post 泛型即 Result.data 的类型：后端 data 就是回复文本
    const reply = await post<string>('/ai/chat', { messages })
    return reply
  },

  // 流式对话：用原生 fetch（axios 不好处理流）+ ReadableStream 逐帧读取
  // onEvent 回调每收到一个事件就被调用一次，由调用方决定怎么展示
  async chatStream(messages: ChatMessage[], onEvent: (event: StreamEvent) => void) {
    // 前端环境变量里的后端地址（与 request.ts 同源配置）；流式不能用 axios，所以要自己拼
    const BASE_URL = import.meta.env.VITE_API_BASE || '/api'
    const token = getToken()
    const resp = await fetch(`${BASE_URL}/ai/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // 手动带 JWT（axios 拦截器管不到原生 fetch）
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ messages }),
    })
    // fetch 只有网络层失败才抛异常，4xx/5xx 要手动判断
    if (!resp.ok || !resp.body) throw new Error(`请求失败（${resp.status}）`)

    const reader = resp.body.getReader() // 逐块读取响应流的读取器
    const decoder = new TextDecoder() // 字节流 → 字符串解码器
    let buf = '' // 半截帧缓冲区：TCP 分块不保证按帧边界切，凑齐再解析

    while (true) {
      const { done, value } = await reader.read()
      if (done) break // 服务端流结束
      // stream: true 处理跨块的多字节字符（如中文被切成两半的情况）
      buf += decoder.decode(value, { stream: true })
      // SSE 帧以空行（\n\n）分隔，按它切帧
      const frames = buf.split('\n\n')
      // 最后一段可能是不完整的半帧，留在缓冲区等下一块拼上
      buf = frames.pop() ?? ''
      for (const frame of frames) {
        const line = frame.trim()
        if (!line.startsWith('data:')) continue // 只处理 data: 开头的帧
        const event = JSON.parse(line.slice(5)) as StreamEvent // 去掉 "data:" 前缀再解析
        onEvent(event)
      }
    }
  },
}
