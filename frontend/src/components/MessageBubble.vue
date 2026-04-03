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
  border-radius: 0;
  animation: slide-up 0.25s ease;
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
  background: rgba(196, 105, 47, 0.1);
  border: 1px solid rgba(196, 105, 47, 0.2);
}

.bubble-user::before {
  background: linear-gradient(90deg, var(--accent), transparent);
}

.bubble-assistant {
  background: rgba(47, 143, 137, 0.08);
  border: 1px solid rgba(47, 143, 137, 0.15);
}

.bubble-assistant::before {
  background: linear-gradient(90deg, var(--teal), transparent);
}

.bubble-system {
  background: rgba(28, 40, 52, 0.06);
  border: 1px solid rgba(28, 40, 52, 0.1);
}

.bubble-system::before {
  background: linear-gradient(90deg, var(--ink-500), transparent);
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

.indicator-user { background: var(--accent); }
.indicator-assistant { background: var(--teal); }
.indicator-system { background: var(--ink-500); }

.role-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink-700);
}

.bubble-content {
  font-size: 0.9rem;
  line-height: 1.65;
  color: var(--ink-950);
  white-space: pre-wrap;
  word-break: break-word;
}

@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>