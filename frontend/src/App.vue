<template>
  <div class="ref-app">
    <div class="app-layout">
      <aside class="rail">
        <div class="brand">
          <div class="brand-mark">GA</div>
          <div class="brand-sub">Gemini Adapter</div>
        </div>

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
      </aside>

      <main class="canvas">
        <ChatPanel
          :messages="chat.messages.value"
          :sending="chat.sending.value"
          @submit="handleSubmit"
        />
      </main>
    </div>
  </div>
</template>

<script setup>
import ControlPanel from './components/ControlPanel.vue'
import ChatPanel from './components/ChatPanel.vue'
import { useChat } from './composables/useChat.js'

const chat = useChat()

function handleSubmit(text, scrollFn) {
  chat.submitPrompt(text, scrollFn)
}
</script>

<style scoped>
.ref-app .app-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  height: 100vh;
  min-height: 100vh;
}

@media (max-width: 900px) {
  .ref-app .app-layout {
    grid-template-columns: 1fr;
  }
}
</style>