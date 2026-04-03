<template>
  <section class="chat-panel card">
    <div class="chat-header">
      <div class="header-left">
        <div class="header-icon">💬</div>
        <h2 class="header-title">对话</h2>
      </div>
      <span class="message-count">{{ messages.length }} 条消息</span>
    </div>

    <div ref="logRef" class="message-log" aria-live="polite">
      <div v-if="messages.length === 0" class="empty-state-chat">
        <div class="empty-icon">✦</div>
        <p class="empty-text">开始对话吧</p>
        <p class="empty-hint">发送消息以测试 Gemini Adapter</p>
      </div>
      <MessageBubble
        v-for="(msg, idx) in messages"
        :key="idx"
        :role="msg.role"
        :content="msg.content"
      />
    </div>

    <form class="composer" @submit.prevent="onSubmit" autocomplete="off">
      <div class="textarea-wrapper">
        <textarea
          id="chat-prompt"
          v-model="prompt"
          rows="3"
          placeholder="输入消息，回车发送（Shift+Enter 换行）"
          :disabled="sending"
          @keydown="onKeydown"
        ></textarea>
      </div>
      <button
        id="chat-send"
        type="submit"
        class="btn-send primary"
        :disabled="sending || !prompt.trim()"
      >
        <span v-if="sending" class="spinner"></span>
        <span v-else class="send-icon">↗</span>
        {{ sending ? '发送中...' : '发送' }}
      </button>
    </form>
  </section>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import MessageBubble from './MessageBubble.vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  sending: { type: Boolean, default: false },
})

const emit = defineEmits(['submit'])

const prompt = ref('')
const logRef = ref(null)

function scrollLog() {
  if (!logRef.value) return
  logRef.value.scrollTop = logRef.value.scrollHeight
}

function onSubmit() {
  const text = prompt.value.trim()
  if (!text || props.sending) return
  emit('submit', text, scrollLog)
  prompt.value = ''
}

function onKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    onSubmit()
  }
}

watch(
  () => props.messages.length,
  async () => {
    await nextTick()
    scrollLog()
  },
)

defineExpose({ scrollLog })
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid rgba(28, 40, 52, 0.12);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  font-size: 1.15rem;
}

.header-title {
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--ink-700);
}

.message-count {
  font-size: 0.75rem;
  color: var(--ink-500);
  font-family: "BodyWithTimesDigits", monospace;
}

.message-log {
  flex: 1;
  overflow-y: auto;
  padding: 18px 22px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-state-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  opacity: 0.6;
}

.empty-icon {
  font-size: 2.5rem;
  margin-bottom: 4px;
}

.empty-text {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--ink-700);
}

.empty-hint {
  font-size: 0.8rem;
  color: var(--ink-500);
}

.composer {
  padding: 16px 22px;
  border-top: 1px solid rgba(28, 40, 52, 0.12);
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.textarea-wrapper {
  flex: 1;
  position: relative;
}

.textarea-wrapper textarea {
  width: 100%;
  resize: vertical;
  min-height: 52px;
  max-height: 200px;
  line-height: 1.55;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(28, 40, 52, 0.2);
  color: var(--ink-950);
  padding: 10px 14px;
  font-size: 0.875rem;
}

.textarea-wrapper textarea:focus {
  outline: none;
  border-color: var(--accent);
}

.btn-send {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 24px;
  font-weight: 600;
  white-space: nowrap;
  min-height: 42px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.btn-send:hover:not(:disabled) {
  transform: translateY(-1px);
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-icon {
  font-size: 1.1rem;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(0, 0, 0, 0.3);
  border-top-color: #111;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>