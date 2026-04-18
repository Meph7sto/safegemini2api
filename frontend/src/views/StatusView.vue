<template>
  <section class="section">
    <div class="section-label">03 / Status</div>
    <h2 class="section-title">运行状态</h2>

    <div class="card-grid">
      <article class="card info-card">
        <p class="eyebrow">Request Status</p>
        <h3>{{ status }}</h3>
        <p>{{ statusError ? '请求或连接存在异常。' : '当前请求链路可用。' }}</p>
      </article>

      <article class="card info-card accent-card">
        <p class="eyebrow">Message Summary</p>
        <h3>{{ messageCount }} 条消息</h3>
        <p>你可以从这里快速确认当前会话是否有上下文积累。</p>
      </article>

      <article class="card info-card">
        <p class="eyebrow">Routing</p>
        <h3>{{ connectionModeLabel }}</h3>
        <p>当前路由方式决定请求会从本地还是远端 Agent 发出。</p>
      </article>
    </div>

    <article class="card guide-card">
      <p class="eyebrow">API Guide</p>
      <h3>如何调用导出的 API</h3>

      <div class="endpoint-list">
        <div class="endpoint-item">
          <strong>聊天接口</strong>
          <code>POST http://127.0.0.1:8000/v1/chat/completions</code>
        </div>
        <div class="endpoint-item">
          <strong>模型列表</strong>
          <code>GET http://127.0.0.1:8000/v1/models</code>
        </div>
        <div class="endpoint-item">
          <strong>健康检查</strong>
          <code>GET http://127.0.0.1:8000/healthz</code>
        </div>
        <div class="endpoint-item">
          <strong>本地 A2A Agent</strong>
          <code>http://127.0.0.1:10000/agent-card</code>
        </div>
      </div>
    </article>
  </section>
</template>

<script setup>
defineProps({
  status: { type: String, default: '就绪' },
  statusError: { type: Boolean, default: false },
  messageCount: { type: Number, default: 0 },
  connectionModeLabel: { type: String, default: '未设置' },
})
</script>
