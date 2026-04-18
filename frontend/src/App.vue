<template>
  <div class="ref-app">
    <nav class="nav">
      <div class="nav-left">
        <button type="button" class="nav-brand-link nav-brand-button" @click="setView('home')">
          <span class="nav-brand">SafeGemini2API</span>
        </button>
      </div>

      <ul class="nav-links">
        <li>
          <button
            type="button"
            class="nav-tab"
            :class="{ active: activeView === 'home' }"
            @click="setView('home')"
          >
            首页
          </button>
        </li>
        <li>
          <button
            type="button"
            class="nav-tab"
            :class="{ active: activeView === 'experience' }"
            @click="setView('experience')"
          >
            体验
          </button>
        </li>
        <li>
          <button
            type="button"
            class="nav-tab"
            :class="{ active: activeView === 'settings' }"
            @click="setView('settings')"
          >
            设置
          </button>
        </li>
        <li>
          <button
            type="button"
            class="nav-tab"
            :class="{ active: activeView === 'status' }"
            @click="setView('status')"
          >
            状态
          </button>
        </li>
      </ul>

      <button type="button" class="nav-cta" @click="setView('settings')">
        连接配置
      </button>
    </nav>

    <div v-if="activeView === 'home'" class="home-screen">
      <section class="hero">
        <h1>
          SafeGemini2API<br>
          <span>控制台</span>
        </h1>
        <p class="hero-intro">
          SafeGemini2API 是一个面向 Gemini CLI 的OpenAI API兼容格式调用的前端控制台，
          用于快速测试对话、切换连接模式、检查运行状态并集中管理配置。
        </p>
        <div class="hero-buttons">
          <button type="button" class="btn-green hero-primary-btn" @click="setView('experience')">
            开始对话
          </button>
          <button type="button" class="btn-subtle hero-secondary-btn" @click="setView('settings')">
            查看设置
          </button>
        </div>
      </section>

      <footer class="home-footer">
        <p>
          GitHub Repository by
          <strong>Meph7sto</strong>
        </p>
        <a
          href="https://github.com/Meph7sto/safegemini2api"
          target="_blank"
          rel="noopener noreferrer"
          class="home-footer-link"
        >
          <svg viewBox="0 0 16 16" aria-hidden="true" class="home-footer-icon">
            <path
              fill="currentColor"
              d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38
              0-.19-.01-.82-.01-1.49-2 .37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13
              -.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66
              .07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15
              -.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0
              1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82
              1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01
              1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"
            />
          </svg>
          github.com/Meph7sto/safegemini2api
        </a>
      </footer>
    </div>

    <template v-else>
      <hr class="section-divider">

      <section v-if="activeView === 'experience'" class="section">
        <div class="section-label">01 / Experience</div>
        <h2 class="section-title">对话体验</h2>

        <div class="card-grid summary-grid">
          <article class="card summary-card">
            <p class="eyebrow">Current Model</p>
            <h3>{{ chat.model.value || 'gemini-2.5-flash' }}</h3>
            <p>当前请求将使用选中的模型，并沿用你的会话标识与连接方式。</p>
          </article>

          <article class="card summary-card">
            <p class="eyebrow">Connection Mode</p>
            <h3>{{ connectionModeLabel }}</h3>
            <p>支持本地 CLI、本地 A2A 和远程 Agent，切换后会立即展示对应体验界面。</p>
          </article>

          <article class="card summary-card">
            <p class="eyebrow">Conversation</p>
            <h3>{{ chat.messages.value.length }} 条消息</h3>
            <p>聊天区域保持在主舞台，避免设置项和消息流混排造成干扰。</p>
          </article>
        </div>

        <div class="card stage-card">
          <ChatPanel
            :messages="chat.messages.value"
            :sending="chat.sending.value"
            @submit="handleSubmit"
          />
        </div>
      </section>

      <section v-else-if="activeView === 'settings'" class="section">
        <div class="section-label">02 / Settings</div>
        <h2 class="section-title">连接设置</h2>

        <div class="settings-layout">
          <div class="card settings-card">
            <ControlPanel
              :apiKey="chat.apiKey.value"
              :model="chat.model.value"
              :sessionKey="chat.sessionKey.value"
              :stream="chat.stream.value"
              :connectionMode="chat.connectionMode.value"
              :agentUrl="chat.agentUrl.value"
              :status="chat.status.value"
              :statusError="chat.statusError.value"
              @update:apiKey="chat.apiKey.value = $event"
              @update:model="chat.model.value = $event"
              @update:sessionKey="chat.sessionKey.value = $event"
              @update:stream="chat.stream.value = $event"
              @update:connectionMode="chat.connectionMode.value = $event"
              @update:agentUrl="chat.agentUrl.value = $event"
              @clear="chat.clearMessages()"
            />
          </div>

          <aside class="settings-side">
            <article class="card info-card">
              <p class="eyebrow">Live Status</p>
              <h3>{{ chat.status.value }}</h3>
              <p>
                {{ chat.statusError.value ? '当前存在连接或请求错误，请检查参数。' : '当前状态正常，可以直接发起对话。' }}
              </p>
            </article>

            <article class="card info-card accent-card">
              <p class="eyebrow">Current Snapshot</p>
              <h3>{{ connectionModeLabel }}</h3>
              <ul class="feature-list">
                <li>模型：{{ chat.model.value || 'gemini-2.5-flash' }}</li>
                <li>流式输出：{{ chat.stream.value ? '已开启' : '已关闭' }}</li>
                <li>消息数量：{{ chat.messages.value.length }}</li>
              </ul>
            </article>
          </aside>
        </div>
      </section>

      <section v-else class="section">
        <div class="section-label">03 / Status</div>
        <h2 class="section-title">运行状态</h2>

        <div class="card-grid">
          <article class="card info-card">
            <p class="eyebrow">Request Status</p>
            <h3>{{ chat.status.value }}</h3>
            <p>{{ chat.statusError.value ? '请求或连接存在异常。' : '当前请求链路可用。' }}</p>
          </article>

          <article class="card info-card accent-card">
            <p class="eyebrow">Message Summary</p>
            <h3>{{ chat.messages.value.length }} 条消息</h3>
            <p>你可以从这里快速确认当前会话是否有上下文积累。</p>
          </article>

          <article class="card info-card">
            <p class="eyebrow">Routing</p>
            <h3>{{ connectionModeLabel }}</h3>
            <p>当前路由方式决定请求会从本地还是远端 Agent 发出。</p>
          </article>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import ControlPanel from './components/ControlPanel.vue'
import ChatPanel from './components/ChatPanel.vue'
import { useChat } from './composables/useChat.js'

const chat = useChat()
const activeView = ref('home')

const connectionModeLabel = computed(() => {
  const labels = {
    local_cli: 'Local CLI',
    local_a2a: 'Local A2A',
    remote_agent: 'Remote Agent',
  }
  return labels[chat.connectionMode.value] || '未设置'
})

function handleSubmit(text, scrollFn) {
  chat.submitPrompt(text, scrollFn)
}

function setView(view) {
  activeView.value = view
}
</script>
