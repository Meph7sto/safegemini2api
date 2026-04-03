<template>
  <div class="app-layout">
    <!-- Header -->
    <header class="app-header">
      <div class="header-content">
        <div class="brand">
          <div class="brand-glow"></div>
          <h1 class="brand-name">Gemini Adapter</h1>
          <span class="brand-badge">Console</span>
        </div>
        <p class="brand-tagline">
          Vue 3 前端 · FastAPI 后端 · OpenAI 兼容接口
        </p>
      </div>
      <div class="header-decoration" aria-hidden="true">
        <span class="deco-dot" style="--c: var(--accent-blue)"></span>
        <span class="deco-dot" style="--c: var(--accent-green)"></span>
        <span class="deco-dot" style="--c: var(--accent-purple)"></span>
        <span class="deco-dot" style="--c: var(--accent-pink)"></span>
        <span class="deco-dot" style="--c: var(--accent-orange)"></span>
      </div>
    </header>

    <!-- Main layout -->
    <main class="main-grid">
      <ControlPanel
        :apiKey="chat.apiKey.value"
        :model="chat.model.value"
        :sessionKey="chat.sessionKey.value"
        :stream="chat.stream.value"
        :status="chat.status.value"
        :statusError="chat.statusError.value"
        @update:apiKey="chat.apiKey.value = $event"
        @update:model="chat.model.value = $event"
        @update:sessionKey="chat.sessionKey.value = $event"
        @update:stream="chat.stream.value = $event"
        @clear="chat.clearMessages()"
      />
      <ChatPanel
        :messages="chat.messages.value"
        :sending="chat.sending.value"
        @submit="handleSubmit"
      />
    </main>
  </div>
</template>

<script setup>
import ControlPanel from './components/ControlPanel.vue'
import ChatPanel from './components/ChatPanel.vue'
import { useChat } from './composables/useChat.js'

const chat = useChat()

function handleSubmit(text, scrollFn) {
  chat.submitPrompt(text, scrollFn)
}
</script>

<style scoped>
/* ── Header ────────────────────────────────────────────────────── */
.app-header {
  padding: 28px 0 20px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  animation: fade-in var(--duration-slow) var(--ease-smooth);
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

.brand-glow {
  position: absolute;
  top: 50%;
  left: -20px;
  width: 80px;
  height: 80px;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.15), transparent);
  border-radius: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}

.brand-name {
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, var(--text-primary) 30%, var(--accent-blue));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-badge {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 3px 10px;
  background: var(--gradient-primary);
  color: #fff;
  border-radius: 20px;
}

.brand-tagline {
  font-size: 0.8rem;
  color: var(--text-muted);
  letter-spacing: 0.02em;
}

.header-decoration {
  display: flex;
  gap: 6px;
  align-items: center;
}

.deco-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  background: var(--c);
  opacity: 0.7;
  transition: opacity var(--duration-normal) var(--ease-smooth);
}

.deco-dot:hover {
  opacity: 1;
  transform: scale(1.3);
}

/* ── Main grid ─────────────────────────────────────────────────── */
.main-grid {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 20px;
  flex: 1;
  min-height: 0;
  padding-bottom: 24px;
  /* Make both columns fill the remaining viewport */
  height: calc(100vh - 120px);
}

/* ── Responsive ────────────────────────────────────────────────── */
@media (max-width: 900px) {
  .app-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .main-grid {
    grid-template-columns: 1fr;
    height: auto;
  }
}
</style>
