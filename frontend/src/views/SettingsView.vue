<template>
  <section class="section">
    <div class="section-label">02 / Settings</div>
    <h2 class="section-title">连接设置</h2>

    <div class="settings-layout">
      <div class="card settings-card">
        <ControlPanel
          :apiKey="apiKey"
          :model="model"
          :sessionKey="sessionKey"
          :stream="stream"
          :connectionMode="connectionMode"
          :agentUrl="agentUrl"
          :status="status"
          :statusError="statusError"
          @update:apiKey="$emit('update:apiKey', $event)"
          @update:model="$emit('update:model', $event)"
          @update:sessionKey="$emit('update:sessionKey', $event)"
          @update:stream="$emit('update:stream', $event)"
          @update:connectionMode="$emit('update:connectionMode', $event)"
          @update:agentUrl="$emit('update:agentUrl', $event)"
          @clear="$emit('clear')"
        />
      </div>

      <aside class="settings-side">
        <article class="card info-card">
          <p class="eyebrow">Live Status</p>
          <h3>{{ status }}</h3>
          <p>
            {{ statusError ? '当前存在连接或请求错误，请检查参数。' : '当前状态正常，可以直接发起对话。' }}
          </p>
        </article>

        <article class="card info-card accent-card">
          <p class="eyebrow">Current Snapshot</p>
          <h3>{{ connectionModeLabel }}</h3>
          <ul class="feature-list">
            <li>模型：{{ model || 'gemini-2.5-flash' }}</li>
            <li>流式输出：{{ stream ? '已开启' : '已关闭' }}</li>
            <li>消息数量：{{ messageCount }}</li>
          </ul>
        </article>
      </aside>
    </div>
  </section>
</template>

<script setup>
import ControlPanel from '../components/ControlPanel.vue'

defineProps({
  apiKey: { type: String, default: '' },
  model: { type: String, default: '' },
  sessionKey: { type: String, default: '' },
  stream: { type: Boolean, default: true },
  connectionMode: { type: String, default: 'local_cli' },
  connectionModeLabel: { type: String, default: '未设置' },
  agentUrl: { type: String, default: '' },
  status: { type: String, default: '就绪' },
  statusError: { type: Boolean, default: false },
  messageCount: { type: Number, default: 0 },
})

defineEmits([
  'update:apiKey',
  'update:model',
  'update:sessionKey',
  'update:stream',
  'update:connectionMode',
  'update:agentUrl',
  'clear',
])
</script>
