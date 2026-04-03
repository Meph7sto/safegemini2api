<template>
  <div class="message-bubble" :class="roleClass">
    <div class="bubble-header">
      <span class="role-indicator" :class="`indicator-${role}`"></span>
      <span class="role-label">{{ roleLabel }}</span>
    </div>
    <div class="bubble-content">{{ content }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  role: { type: String, required: true },
  content: { type: String, default: '' },
})

const roleClass = computed(() => `bubble-${props.role}`)

const roleLabel = computed(() => {
  const labels = { user: 'You', assistant: 'Assistant', system: 'System' }
  return labels[props.role] || props.role.toUpperCase()
})
</script>

<style scoped>
.message-bubble {
  padding: 16px 18px;
  border-radius: var(--radius-md);
  animation: slide-up var(--duration-normal) var(--ease-smooth);
  position: relative;
  overflow: hidden;
}

.message-bubble::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  opacity: 0.5;
}

.bubble-user {
  background: rgba(106, 168, 254, 0.08);
  border: 1px solid rgba(106, 168, 254, 0.15);
}

.bubble-user::before {
  background: linear-gradient(90deg, var(--accent-blue), transparent);
}

.bubble-assistant {
  background: rgba(74, 222, 128, 0.06);
  border: 1px solid rgba(74, 222, 128, 0.12);
}

.bubble-assistant::before {
  background: linear-gradient(90deg, var(--accent-green), transparent);
}

.bubble-system {
  background: rgba(167, 139, 250, 0.06);
  border: 1px solid rgba(167, 139, 250, 0.12);
}

.bubble-system::before {
  background: linear-gradient(90deg, var(--accent-purple), transparent);
}

.bubble-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.role-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.indicator-user { background: var(--accent-blue); }
.indicator-assistant { background: var(--accent-green); }
.indicator-system { background: var(--accent-purple); }

.role-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
}

.bubble-content {
  font-size: 0.9rem;
  line-height: 1.65;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
