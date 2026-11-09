// AI 对话模块
// 后端已实现：
//   POST /api/ai/chat  { messages: ChatMessage[] } → data 为回复字符串本身
// （后端 service 返回 Result.success(回复文本)，没有 {reply} 这层包装）

import { post } from '@/utils/request'
import type { ChatMessage } from './types'

export const aiApi = {
  async chat(messages: ChatMessage[]): Promise<string> {
    // post 泛型即 Result.data 的类型：后端 data 就是回复文本
    const reply = await post<string>('/ai/chat', { messages })
    return reply
  },
}
