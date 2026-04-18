<template>
  <section class="chat-panel">
    <div class="chat-header">
      <div>
        <p class="panel-kicker">Conversation Stage</p>
        <h3 class="panel-title">对话面板</h3>
      </div>
      <span class="message-count">{{ messages.length }} 条消息</span>
    </div>

    <div ref="logRef" class="message-log" aria-live="polite">
      <div v-if="messages.length === 0" class="empty-state-chat">
        <p class="empty-title">Start with a prompt</p>
        <p class="empty-hint">输入一条消息，验证当前配置与响应链路。</p>
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
        <label class="composer-label" for="chat-prompt">Message</label>
        <textarea
          id="chat-prompt"
          v-model="prompt"
          rows="4"
          placeholder="输入消息，回车发送（Shift+Enter 换行）"
          :disabled="sending"
          @keydown="onKeydown"
        ></textarea>
      </div>
      <button
        id="chat-send"
        type="submit"
        class="btn-green composer-btn"
        :disabled="sending || !prompt.trim()"
      >
        <span v-if="sending" class="spinner"></span>
        <span v-else>{{ '发送消息' }}</span>
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
