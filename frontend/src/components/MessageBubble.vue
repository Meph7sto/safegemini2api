<template>
  <article class="message-bubble" :class="roleClass">
    <div class="bubble-header">
      <span class="role-label">{{ roleLabel }}</span>
    </div>
    <div class="bubble-content">{{ content }}</div>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  role: { type: String, required: true },
  content: { type: String, default: '' },
})

const roleClass = computed(() => `bubble-${props.role}`)

const roleLabel = computed(() => {
  const labels = { user: '你', assistant: '助手', system: '系统' }
  return labels[props.role] || props.role.toUpperCase()
})
</script>
