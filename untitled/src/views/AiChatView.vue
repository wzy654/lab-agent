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
    content: '你好，我是实验室智能助手。可以帮你查询空闲实验室、推荐设备、解答预约规则，试试问我"明天上午有哪些实验室空闲？"',
  },
])
const input = ref('')
const sending = ref(false)
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

  try {
    // 对接后端 LangGraph：POST /api/ai/chat
    const reply = await aiApi.chat(messages.value.map(({ role, content }) => ({ role, content })))
    messages.value.push({ role: 'assistant', content: reply })
  } catch {
    messages.value.push({
      role: 'assistant',
      content: '抱歉，AI 服务暂时不可用，请确认后端 /api/ai/chat 接口已启动。',
    })
  } finally {
    sending.value = false
    scrollBottom()
  }
}
</script>

<template>
  <div class="chat-page">
    <div class="chat-header">
      <h2>AI 智能助手</h2>
      <el-tag size="small" effect="plain">LangGraph 驱动</el-tag>
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
      <div v-if="sending" class="chat-row is-ai">
        <div class="bubble typing">对方正在输入…</div>
      </div>
    </div>

    <div class="chat-input">
      <el-input
        v-model="input"
        placeholder="输入你的问题，例如：明天下午 3 点有空的实验室？"
        size="large"
        @keyup.enter="send"
      />
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

.chat-input {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}
</style>
