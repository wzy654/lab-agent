<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { Promotion } from '@element-plus/icons-vue'
import { aiApi } from '@/api/ai'
import type { ChatMessage } from '@/api/types'

interface Message {
  role: 'user' | 'assistant'
  content: string
}
const messages = ref<Message[]>([
  {
    role: 'assistant',
    content: '你好，我是实验室智能助手。可以帮你查询空闲实验室、推荐设备、解答预约规则或者直接预约实验室，试试问我"明天上午有哪些实验室空闲？"',
  },
])
const input = ref('')
const sending = ref(false)
const statusText = ref('') // 工具调用过程文案（如「查询开放实验室…」），流式期间展示
const useStream = ref(true) // 是否开启流式输出：开=打字机+过程可见，关=一次性返回
const listRef = ref<HTMLElement>()

async function scrollBottom() {
  await nextTick()
  listRef.value?.scrollTo({ top: listRef.value.scrollHeight, behavior: 'smooth' })
}

async function send() {
  const text = input.value.trim()
  if (!text || sending.value) return
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  sending.value = true
  scrollBottom()

  // 预先占位一条空的 AI 回复：流式期间每个 token 事件往里追加，实现打字机效果
  messages.value.push({ role: 'assistant', content: '' })
  const last = messages.value[messages.value.length - 1]

  try {
    // 发给后端的历史不含最后这条空占位（slice 去掉），避免模型把空消息当上下文
    const history = messages.value
      .slice(0, -1)
      .filter((m) => m.content.trim())
      .map(({ role, content }) => ({ role, content }))

    if (useStream.value) {
      // 流式模式：POST /ai/chat/stream，逐事件更新气泡
      await aiApi.chatStream(history, (event) => {
        if (event.type === 'status') {
          statusText.value = event.message
        } else if (event.type === 'tool_start') {
          // 后端 message 已是中文文案（TOOL_LABELS 映射），直接展示
          statusText.value = `${event.message}…`
          // 过渡语和正式回答之间留个分隔，避免混成一坨
          if (last.content) last.content += '\n\n'
          scrollBottom()
        } else if (event.type === 'tool_end') {
          statusText.value = '整理回答中…'
        } else if (event.type === 'token') {
          last.content += event.content
          scrollBottom()
        } else if (event.type === 'error') {
          last.content += (last.content ? '\n\n' : '') + `抱歉，回复失败：${event.message}`
        }
        // done 事件无需处理，finally 里统一收尾
      })
    } else {
      // 非流式模式：POST /ai/chat，一次性拿完整回复
      statusText.value = '正在思考'
      last.content = await aiApi.chat(history)
    }
  } catch (e) {
    // 请求发不出去（断网/超时/4xx）时走这里；流内 error 事件上面已经处理
    const detail = e instanceof Error && e.message ? e.message : 'AI 服务暂时不可用'
    last.content = `抱歉，回复失败：${detail}`
  } finally {
    // 收尾：清状态文案；回答全程为空时兜底一句，避免气泡空白
    statusText.value = ''
    if (!last.content.trim()) last.content = '抱歉，回复失败：AI 服务暂时不可用'
    sending.value = false
    scrollBottom()
  }
}
</script>

<template>
  <div class="chat-page">
    <div class="chat-header">
      <h2>AI 智能助手</h2>
      <el-tag size="small" effect="plain">实验室预约助手</el-tag>
    </div>

    <div ref="listRef" class="chat-list">
      <div
        v-for="(m, i) in messages"
        :key="i"
        class="chat-row"
        :class="m.role === 'user' ? 'is-user' : 'is-ai'"
      >
        <div class="bubble">{{ m.content }}</div>
      </div>
      <div v-if="sending && statusText" class="chat-row is-ai">
        <div class="status-chip">{{ statusText }}</div>
      </div>
    </div>

    <div class="chat-input">
      <el-input
        v-model="input"
        placeholder="输入你的问题，例如：明天下午 3 点有空的实验室？"
        size="large"
        @keyup.enter="send"
      />
      <!-- 流式输出开关：开=打字机逐字显示+工具过程可见，关=一次性返回完整回答 -->
      <div class="stream-toggle" title="切换流式/一次性输出">
        <el-switch v-model="useStream" size="small" />
        <span>流式</span>
      </div>
      <el-button type="primary" size="large" :icon="Promotion" :loading="sending" @click="send">
        发送
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 24px 32px;
  box-sizing: border-box;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.chat-header h2 {
  font-size: 20px;
  color: #1f2d3d;
}

.chat-list {
  flex: 1;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #e8ebee;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.chat-row {
  display: flex;
}

.chat-row.is-user {
  justify-content: flex-end;
}

.bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.is-ai .bubble {
  background: #f4f6f8;
  color: #1f2d3d;
  border-top-left-radius: 2px;
}

.is-user .bubble {
  background: #1f6feb;
  color: #fff;
  border-top-right-radius: 2px;
}

.typing {
  color: #8492a6;
}

/* 工具调用过程的小标签：比气泡更轻量，展示「查询开放实验室…」这类过程文案 */
.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  color: #8492a6;
  background: #f4f6f8;
  border: 1px solid #e8ebee;
}

.chat-input {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}

/* 流式开关：开关+文字纵向居中，放在输入框和发送按钮之间 */
.stream-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.stream-toggle span {
  font-size: 13px;
  color: #8492a6;
}
</style>
