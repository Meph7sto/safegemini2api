<template>
  <section class="section">
    <div class="section-label">01 / Experience</div>
    <h2 class="section-title">对话体验</h2>

    <div class="card-grid summary-grid">
      <article class="card summary-card">
        <p class="eyebrow">Current Model</p>
        <h3>{{ model || 'gemini-2.5-flash' }}</h3>
        <p>当前请求将使用选中的模型，并沿用你的会话标识与连接方式。</p>
      </article>

      <article class="card summary-card">
        <p class="eyebrow">Connection Mode</p>
        <h3>{{ connectionModeLabel }}</h3>
        <p>支持本地 CLI、本地 A2A 和远程 Agent，切换后会立即展示对应体验界面。</p>
      </article>

      <article class="card summary-card">
        <p class="eyebrow">Conversation</p>
        <h3>{{ messages.length }} 条消息</h3>
        <p>聊天区域保持在主舞台，避免设置项和消息流混排造成干扰。</p>
      </article>
    </div>

    <div class="card stage-card">
      <ChatPanel
        :messages="messages"
        :sending="sending"
        @submit="forwardSubmit"
      />
    </div>
  </section>
</template>

<script setup>
import ChatPanel from '../components/ChatPanel.vue'

defineProps({
  messages: { type: Array, default: () => [] },
  sending: { type: Boolean, default: false },
  model: { type: String, default: '' },
  connectionModeLabel: { type: String, default: '未设置' },
})

const emit = defineEmits(['submit'])

function forwardSubmit(text, scrollFn) {
  emit('submit', text, scrollFn)
}
</script>
