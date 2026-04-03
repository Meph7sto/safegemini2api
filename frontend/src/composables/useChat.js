/**
 * Chat logic composable – manages messages, API calls, and streaming.
 *
 * All state is reactive; every update creates new objects (immutable pattern).
 */

import { ref, nextTick } from 'vue'

export function useChat() {
  const messages = ref([])
  const status = ref('就绪')
  const statusError = ref(false)
  const sending = ref(false)

  // ── Settings (reactive, bound to ControlPanel) ──
  const apiKey = ref('')
  const model = ref('gemini-2.5-flash')
  const sessionKey = ref('')
  const stream = ref(true)
  const connectionMode = ref('local_cli')
  const agentUrl = ref('')

  function setStatus(text, isError = false) {
    status.value = text
    statusError.value = isError
  }

  function clearMessages() {
    messages.value = []
    setStatus('已清空')
  }

  function _buildHeaders() {
    const headers = { 'content-type': 'application/json' }
    if (apiKey.value.trim()) {
      headers.authorization = `Bearer ${apiKey.value.trim()}`
    }
    if (sessionKey.value.trim()) {
      headers['x-session-id'] = sessionKey.value.trim()
    }
    return headers
  }

  function _buildBody(outboundMessages) {
    const payload = {
      model: model.value.trim() || 'gemini-2.5-flash',
      stream: stream.value,
      messages: outboundMessages,
      connection_mode: connectionMode.value,
    }
    if (sessionKey.value.trim()) {
      payload.user = sessionKey.value.trim()
    }
    if (connectionMode.value === 'remote_agent' && agentUrl.value.trim()) {
      payload.agent_url = agentUrl.value.trim()
    }
    return payload
  }

  async function _readStreamResponse(response, assistantMsg) {
    if (!response.body) {
      throw new Error('Stream body is empty')
    }
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const frames = buffer.split('\n\n')
      buffer = frames.pop() || ''

      for (const frame of frames) {
        const dataLine = frame
          .split('\n')
          .find((line) => line.startsWith('data:'))
        if (!dataLine) continue

        const raw = dataLine.slice(5).trim()
        if (!raw || raw === '[DONE]') continue

        const payload = JSON.parse(raw)
        if (payload.error) {
          throw new Error(payload.error.message || 'Unknown stream error')
        }
        const delta = payload.choices?.[0]?.delta?.content || ''
        if (!delta) continue

        // Create new message object (immutable update)
        const updated = { ...assistantMsg, content: assistantMsg.content + delta }
        assistantMsg.content = updated.content
        messages.value = [...messages.value.slice(0, -1), { ...assistantMsg }]
        await nextTick()
      }
    }
  }

  async function sendMessage(text, scrollFn) {
    // Add user message (new array)
    messages.value = [...messages.value, { role: 'user', content: text }]
    await nextTick()
    scrollFn?.()

    const outboundMessages = messages.value.map((m) => ({ ...m }))
    const assistantMsg = { role: 'assistant', content: '' }
    messages.value = [...messages.value, { ...assistantMsg }]
    await nextTick()
    scrollFn?.()

    const response = await fetch('/v1/chat/completions', {
      method: 'POST',
      headers: _buildHeaders(),
      body: JSON.stringify(_buildBody(outboundMessages)),
    })

    if (!response.ok) {
      const payload = await response.json().catch(() => ({}))
      const message = payload?.error?.message || `HTTP ${response.status}`
      throw new Error(message)
    }

    if (stream.value) {
      await _readStreamResponse(response, assistantMsg)
      scrollFn?.()
      return
    }

    const payload = await response.json()
    const content = payload.choices?.[0]?.message?.content || ''
    messages.value = [
      ...messages.value.slice(0, -1),
      { role: 'assistant', content },
    ]
    await nextTick()
    scrollFn?.()
  }

  async function submitPrompt(text, scrollFn) {
    const trimmed = text.trim()
    if (!trimmed || sending.value) return

    sending.value = true
    setStatus('发送中...')

    try {
      await sendMessage(trimmed, scrollFn)
      setStatus('已完成')
    } catch (error) {
      // Remove failed assistant message (immutable)
      messages.value = messages.value.slice(0, -1)
      setStatus(`失败：${error.message}`, true)
      await nextTick()
      scrollFn?.()
    } finally {
      sending.value = false
    }
  }

  return {
    messages,
    status,
    statusError,
    sending,
    apiKey,
    model,
    sessionKey,
    stream,
    connectionMode,
    agentUrl,
    setStatus,
    clearMessages,
    submitPrompt,
  }
}
