// AI 对话模块（对接 LangGraph）
// 后端需实现：
//   POST /api/ai/chat  { messages: ChatMessage[] } → { reply: string }
// 若改用 SSE 流式返回，可在此封装 EventSource / fetch stream

import { post } from './request'
import type { ChatMessage } from './types'

export const aiApi = {
  async chat(messages: ChatMessage[]): Promise<string> {
    const data = await post<{ reply: string }>('/ai/chat', { messages })
    return data.reply
  },
}
