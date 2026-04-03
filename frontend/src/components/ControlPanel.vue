<template>
  <aside class="control-panel glass-card">
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
  </aside>
</template>

<script setup>
defineProps({
  apiKey: { type: String, default: '' },
  model: { type: String, default: '' },
  sessionKey: { type: String, default: '' },
  stream: { type: Boolean, default: true },
  status: { type: String, default: '就绪' },
  statusError: { type: Boolean, default: false },
})

defineEmits([
  'update:apiKey',
  'update:model',
  'update:sessionKey',
  'update:stream',
  'clear',
])
</script>

<style scoped>
.control-panel {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  animation: slide-in-left var(--duration-slow) var(--ease-smooth);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border-subtle);
}

.panel-icon {
  font-size: 1.25rem;
}

.panel-title {
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-secondary);
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-secondary);
  letter-spacing: 0.02em;
}

.input-wrapper {
  position: relative;
}

.input-wrapper input {
  width: 100%;
  padding-right: 36px;
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

/* ── Custom Toggle ── */
.toggle-row {
  padding: 4px 0;
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
  background: var(--bg-tertiary);
  border: 1px solid var(--border-medium);
  border-radius: 11px;
  transition: all var(--duration-normal) var(--ease-smooth);
}

.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  background: var(--text-muted);
  border-radius: 50%;
  transition: all var(--duration-normal) var(--ease-smooth);
}

.toggle-label input:checked + .toggle-track {
  background: rgba(106, 168, 254, 0.2);
  border-color: var(--accent-blue);
}

.toggle-label input:checked + .toggle-track .toggle-thumb {
  left: 20px;
  background: var(--accent-blue);
  box-shadow: 0 0 8px rgba(106, 168, 254, 0.4);
}

.toggle-text {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

/* ── Clear button ── */
.btn-clear {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
}

.btn-clear:hover {
  background: var(--bg-elevated);
  border-color: var(--border-medium);
  color: var(--text-primary);
}

.btn-icon {
  font-size: 0.9rem;
}

/* ── Status bar ── */
.status-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(74, 222, 128, 0.06);
  border: 1px solid rgba(74, 222, 128, 0.1);
  border-radius: var(--radius-sm);
  transition: all var(--duration-normal) var(--ease-smooth);
}

.status-bar.status-error {
  background: rgba(248, 113, 113, 0.08);
  border-color: rgba(248, 113, 113, 0.15);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-green);
  animation: pulse-glow 2s ease-in-out infinite;
}

.status-dot.dot-error {
  background: var(--accent-red);
}

.status-text {
  font-size: 0.8rem;
  color: var(--text-secondary);
}
</style>
