<template>
  <div class="control-panel">
    <div class="panel-heading">
      <p class="panel-kicker">Connection Parameters</p>
      <h3 class="panel-title">连接参数</h3>
      <p class="panel-copy">将 API、模型和 Agent 连接配置收拢到一个区域，便于集中调整。</p>
    </div>

    <div class="form-group">
      <label class="form-label" for="ctrl-api-key">API Key</label>
      <input
        id="ctrl-api-key"
        class="form-input"
        :value="apiKey"
        type="password"
        placeholder="可留空"
        autocomplete="off"
        @input="$emit('update:apiKey', $event.target.value)"
      >
    </div>

    <div class="form-group">
      <label class="form-label" for="ctrl-model">Model</label>
      <input
        id="ctrl-model"
        class="form-input"
        :value="model"
        type="text"
        @input="$emit('update:model', $event.target.value)"
      >
    </div>

    <div class="form-group">
      <label class="form-label" for="ctrl-session">Session Key</label>
      <input
        id="ctrl-session"
        class="form-input"
        :value="sessionKey"
        type="text"
        placeholder="建议每个聊天唯一"
        @input="$emit('update:sessionKey', $event.target.value)"
      >
    </div>

    <div class="form-group">
      <span class="form-label">Connection Mode</span>
      <div class="mode-switch">
        <button
          type="button"
          class="mode-btn"
          :class="{ active: connectionMode === 'local_cli' }"
          @click="$emit('update:connectionMode', 'local_cli')"
        >
          Local CLI
        </button>
        <button
          type="button"
          class="mode-btn"
          :class="{ active: connectionMode === 'local_a2a' }"
          @click="$emit('update:connectionMode', 'local_a2a')"
        >
          Local A2A
        </button>
        <button
          type="button"
          class="mode-btn"
          :class="{ active: connectionMode === 'remote_agent' }"
          @click="$emit('update:connectionMode', 'remote_agent')"
        >
          Remote Agent
        </button>
      </div>
    </div>

    <div v-if="connectionMode === 'local_a2a'" class="form-group">
      <label class="form-label">Agent URL</label>
      <input
        class="form-input form-input-static"
        value="http://localhost:10000"
        type="text"
        disabled
      >
      <div class="form-state-label">Local A2A Agent (auto)</div>
    </div>

    <div v-if="connectionMode === 'remote_agent'" class="form-group">
      <label class="form-label" for="ctrl-agent-url">Agent URL</label>
      <input
        id="ctrl-agent-url"
        class="form-input"
        :value="agentUrl"
        type="text"
        placeholder="https://agent.example.com/agent-card"
        @input="$emit('update:agentUrl', $event.target.value)"
      >
    </div>

    <div class="toggle-row">
      <label class="toggle-label" for="ctrl-stream">
        <input
          id="ctrl-stream"
          type="checkbox"
          :checked="stream"
          @change="$emit('update:stream', $event.target.checked)"
        >
        <span class="toggle-text">流式输出</span>
        <span class="toggle-chip">{{ stream ? 'On' : 'Off' }}</span>
      </label>
    </div>

    <div class="action-row">
      <button
        id="ctrl-clear"
        class="btn-subtle danger-soft"
        type="button"
        @click="$emit('clear')"
      >
        清空对话
      </button>
    </div>

    <div class="status-box" :class="{ error: statusError }">
      <span class="status-dot"></span>
      <span>{{ status }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  apiKey: { type: String, default: '' },
  model: { type: String, default: '' },
  sessionKey: { type: String, default: '' },
  stream: { type: Boolean, default: true },
  connectionMode: { type: String, default: 'local_cli' },
  agentUrl: { type: String, default: '' },
  status: { type: String, default: '就绪' },
  statusError: { type: Boolean, default: false },
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
