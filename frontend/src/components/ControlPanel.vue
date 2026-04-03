<template>
  <div class="control-panel">
    <div class="panel-header">
      <div class="panel-icon">⚙</div>
      <h2 class="panel-title">连接参数</h2>
    </div>

    <div class="field-group">
      <label class="field-label" for="ctrl-api-key">API Key</label>
      <div class="input-wrapper">
        <input
          id="ctrl-api-key"
          :value="apiKey"
          type="password"
          placeholder="可留空"
          autocomplete="off"
          @input="$emit('update:apiKey', $event.target.value)"
        />
        <span class="input-icon">🔑</span>
      </div>
    </div>

    <div class="field-group">
      <label class="field-label" for="ctrl-model">Model</label>
      <div class="input-wrapper">
        <input
          id="ctrl-model"
          :value="model"
          type="text"
          @input="$emit('update:model', $event.target.value)"
        />
        <span class="input-icon">🤖</span>
      </div>
    </div>

    <div class="field-group">
      <label class="field-label" for="ctrl-session">Session Key</label>
      <div class="input-wrapper">
        <input
          id="ctrl-session"
          :value="sessionKey"
          type="text"
          placeholder="建议每个聊天唯一"
          @input="$emit('update:sessionKey', $event.target.value)"
        />
        <span class="input-icon">🏷</span>
      </div>
    </div>

    <div class="mode-switch">
      <button
        type="button"
        class="mode-btn"
        :class="{ active: connectionMode === 'local_cli' }"
        @click="$emit('update:connectionMode', 'local_cli')"
      >
        <span class="mode-icon">💻</span>
        <span class="mode-label">Local CLI</span>
      </button>
      <button
        type="button"
        class="mode-btn"
        :class="{ active: connectionMode === 'local_a2a' }"
        @click="$emit('update:connectionMode', 'local_a2a')"
      >
        <span class="mode-icon">🔗</span>
        <span class="mode-label">Local A2A</span>
      </button>
      <button
        type="button"
        class="mode-btn"
        :class="{ active: connectionMode === 'remote_agent' }"
        @click="$emit('update:connectionMode', 'remote_agent')"
      >
        <span class="mode-icon">🌐</span>
        <span class="mode-label">Remote Agent</span>
      </button>
    </div>

    <div v-if="connectionMode === 'local_a2a'" class="field-group local-a2a-field">
      <label class="field-label">Agent URL</label>
      <div class="input-wrapper">
        <input
          value="http://localhost:10000"
          type="text"
          disabled
          class="input-hint"
        />
        <span class="input-icon">🔗</span>
      </div>
      <span class="field-hint">Local A2A Agent (auto)</span>
    </div>

    <div v-if="connectionMode === 'remote_agent'" class="field-group remote-field">
      <label class="field-label" for="ctrl-agent-url">Agent URL</label>
      <div class="input-wrapper">
        <input
          id="ctrl-agent-url"
          :value="agentUrl"
          type="text"
          placeholder="https://agent.example.com/agent-card"
          @input="$emit('update:agentUrl', $event.target.value)"
        />
        <span class="input-icon">🔗</span>
      </div>
    </div>

    <div class="toggle-row">
      <label class="toggle-label" for="ctrl-stream">
        <input
          id="ctrl-stream"
          type="checkbox"
          :checked="stream"
          @change="$emit('update:stream', $event.target.checked)"
        />
        <span class="toggle-track">
          <span class="toggle-thumb"></span>
        </span>
        <span class="toggle-text">流式输出</span>
      </label>
    </div>

    <button
      id="ctrl-clear"
      class="btn-clear"
      type="button"
      @click="$emit('clear')"
    >
      <span class="btn-icon">✦</span>
      清空对话
    </button>

    <div class="status-bar" :class="{ 'status-error': statusError }">
      <span class="status-dot" :class="{ 'dot-error': statusError }"></span>
      <span class="status-text">{{ status }}</span>
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

<style scoped>
.control-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(28, 40, 52, 0.12);
}

.panel-icon {
  font-size: 1.25rem;
}

.panel-title {
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--ink-700);
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--ink-700);
  letter-spacing: 0.02em;
}

.input-wrapper {
  position: relative;
}

.input-wrapper input {
  width: 100%;
  padding-right: 36px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(28, 40, 52, 0.2);
  color: var(--ink-950);
  padding: 10px 12px;
  font-size: 13px;
}

.input-wrapper input:focus {
  outline: none;
  border-color: var(--accent);
}

.input-icon {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.85rem;
  opacity: 0.5;
  pointer-events: none;
}

.toggle-row {
  padding: 4px 0;
}

.mode-switch {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.mode-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 8px;
  border: 1px solid rgba(28, 40, 52, 0.2);
  background: rgba(255, 255, 255, 0.5);
  color: rgba(28, 40, 52, 0.6);
  cursor: pointer;
  font-size: 11px;
  transition: all 0.25s ease;
}

.mode-btn:hover {
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(28, 40, 52, 0.3);
}

.mode-btn.active {
  background: rgba(196, 105, 47, 0.15);
  color: var(--ink-950);
  border-color: rgba(196, 105, 47, 0.6);
}

.mode-icon {
  font-size: 1.1rem;
}

.mode-label {
  font-weight: 500;
}

.remote-field,
.local-a2a-field {
  animation: fadeIn 0.25s ease;
}

.local-a2a-field .input-hint {
  background: rgba(28, 40, 52, 0.05);
  color: rgba(28, 40, 52, 0.6);
  cursor: not-allowed;
}

.field-hint {
  font-size: 0.75rem;
  color: rgba(28, 40, 52, 0.5);
  margin-top: 4px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}

.toggle-label input {
  display: none;
}

.toggle-track {
  position: relative;
  width: 40px;
  height: 22px;
  background: rgba(28, 40, 52, 0.1);
  border: 1px solid rgba(28, 40, 52, 0.2);
  border-radius: 11px;
  transition: all 0.25s ease;
}

.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  background: var(--ink-500);
  border-radius: 50%;
  transition: all 0.25s ease;
}

.toggle-label input:checked + .toggle-track {
  background: rgba(196, 105, 47, 0.2);
  border-color: var(--accent);
}

.toggle-label input:checked + .toggle-track .toggle-thumb {
  left: 20px;
  background: var(--accent);
}

.toggle-text {
  font-size: 0.85rem;
  color: var(--ink-700);
}

.btn-clear {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: transparent;
  border: 1px solid rgba(196, 91, 96, 0.55);
  color: #3a0e10;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.25s ease;
}

.btn-clear:hover {
  background: rgba(196, 91, 96, 0.15);
}

.btn-icon {
  font-size: 0.9rem;
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(47, 143, 137, 0.08);
  border: 1px solid rgba(47, 143, 137, 0.15);
  transition: all 0.25s ease;
}

.status-bar.status-error {
  background: rgba(196, 91, 96, 0.08);
  border-color: rgba(196, 91, 96, 0.15);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--teal);
  animation: pulse-glow 2s ease-in-out infinite;
}

.status-dot.dot-error {
  background: var(--signal);
}

.status-text {
  font-size: 0.8rem;
  color: var(--ink-700);
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}
</style>