<template>
  <nav class="nav">
    <div class="nav-left">
      <button type="button" class="nav-brand-link nav-brand-button" @click="$emit('navigate', 'home')">
        <span class="nav-brand">SafeGemini2API</span>
      </button>
    </div>

    <ul class="nav-links">
      <li v-for="item in navItems" :key="item.key">
        <button
          type="button"
          class="nav-tab"
          :class="{ active: activeView === item.key }"
          @click="$emit('navigate', item.key)"
        >
          {{ item.label }}
        </button>
      </li>
    </ul>

    <button type="button" class="nav-cta" @click="$emit('navigate', 'settings')">
      连接配置
    </button>
  </nav>
</template>

<script setup>
defineProps({
  activeView: { type: String, required: true },
})

defineEmits(['navigate'])

const navItems = [
  { key: 'home', label: '首页' },
  { key: 'experience', label: '体验' },
  { key: 'settings', label: '设置' },
  { key: 'status', label: '状态' },
]
</script>
