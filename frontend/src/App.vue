<template>
  <div class="ref-app">
    <AppNavigation
      :activeView="activeView"
      @navigate="setView"
    />

    <HomeView
      v-if="activeView === 'home'"
      @navigate="setView"
    />

    <template v-else>
      <hr class="section-divider">

      <ExperienceView
        v-if="activeView === 'experience'"
        :messages="chat.messages.value"
        :sending="chat.sending.value"
        :model="chat.model.value"
        :connectionModeLabel="connectionModeLabel"
        @submit="handleSubmit"
      />

      <SettingsView
        v-else-if="activeView === 'settings'"
        :apiKey="chat.apiKey.value"
        :model="chat.model.value"
        :sessionKey="chat.sessionKey.value"
        :stream="chat.stream.value"
        :connectionMode="chat.connectionMode.value"
        :connectionModeLabel="connectionModeLabel"
        :agentUrl="chat.agentUrl.value"
        :status="chat.status.value"
        :statusError="chat.statusError.value"
        :messageCount="chat.messages.value.length"
        @update:apiKey="chat.apiKey.value = $event"
        @update:model="chat.model.value = $event"
        @update:sessionKey="chat.sessionKey.value = $event"
        @update:stream="chat.stream.value = $event"
        @update:connectionMode="chat.connectionMode.value = $event"
        @update:agentUrl="chat.agentUrl.value = $event"
        @clear="chat.clearMessages()"
      />

      <StatusView
        v-else
        :status="chat.status.value"
        :statusError="chat.statusError.value"
        :messageCount="chat.messages.value.length"
        :connectionModeLabel="connectionModeLabel"
      />
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import AppNavigation from './components/AppNavigation.vue'
import { useChat } from './composables/useChat.js'
import ExperienceView from './views/ExperienceView.vue'
import HomeView from './views/HomeView.vue'
import SettingsView from './views/SettingsView.vue'
import StatusView from './views/StatusView.vue'

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
