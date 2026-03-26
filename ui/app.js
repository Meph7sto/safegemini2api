const { createApp, nextTick } = window.Vue;

createApp({
  data() {
    return {
      apiKey: "",
      model: "gemini-2.5-flash",
      sessionKey: "",
      stream: true,
      status: "就绪",
      statusError: false,
      prompt: "",
      sending: false,
      messages: []
    };
  },
  methods: {
    setStatus(text, isError = false) {
      this.status = text;
      this.statusError = isError;
    },
    clearMessages() {
      this.messages = [];
      this.setStatus("已清空");
      this.scrollLog();
    },
    requestHeaders() {
      const headers = {
        "content-type": "application/json"
      };
      if (this.apiKey.trim()) {
        headers.authorization = `Bearer ${this.apiKey.trim()}`;
      }
      if (this.sessionKey.trim()) {
        headers["x-session-id"] = this.sessionKey.trim();
      }
      return headers;
    },
    requestBody(outboundMessages) {
      const payload = {
        model: this.model.trim() || "gemini-2.5-flash",
        stream: this.stream,
        messages: outboundMessages
      };
      if (this.sessionKey.trim()) {
        payload.user = this.sessionKey.trim();
      }
      return payload;
    },
    async readStreamResponse(response, assistant) {
      if (!response.body) {
        throw new Error("Stream body is empty");
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const chunk = await reader.read();
        if (chunk.done) {
          break;
        }
        buffer += decoder.decode(chunk.value, { stream: true });
        const frames = buffer.split("\n\n");
        buffer = frames.pop() || "";

        for (const frame of frames) {
          const dataLine = frame
            .split("\n")
            .find((line) => line.startsWith("data:"));
          if (!dataLine) {
            continue;
          }
          const raw = dataLine.slice(5).trim();
          if (!raw || raw === "[DONE]") {
            continue;
          }
          const payload = JSON.parse(raw);
          if (payload.error) {
            throw new Error(payload.error.message || "Unknown stream error");
          }
          const delta = payload.choices?.[0]?.delta?.content || "";
          if (!delta) {
            continue;
          }
          assistant.content += delta;
          await nextTick();
          this.scrollLog();
        }
      }
    },
    async sendMessage(text) {
      this.messages.push({
        role: "user",
        content: text
      });
      await nextTick();
      this.scrollLog();

      const outboundMessages = [...this.messages];
      const assistant = {
        role: "assistant",
        content: ""
      };
      this.messages.push(assistant);
      await nextTick();
      this.scrollLog();

      const response = await fetch("/v1/chat/completions", {
        method: "POST",
        headers: this.requestHeaders(),
        body: JSON.stringify(this.requestBody(outboundMessages))
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        const message = payload?.error?.message || `HTTP ${response.status}`;
        throw new Error(message);
      }

      if (this.stream) {
        await this.readStreamResponse(response, assistant);
        return;
      }

      const payload = await response.json();
      assistant.content = payload.choices?.[0]?.message?.content || "";
      await nextTick();
      this.scrollLog();
    },
    async submitPrompt() {
      const text = this.prompt.trim();
      if (!text || this.sending) {
        return;
      }

      this.sending = true;
      this.prompt = "";
      this.setStatus("发送中...");

      try {
        await this.sendMessage(text);
        this.setStatus("已完成");
      } catch (error) {
        this.messages.pop();
        this.setStatus(`失败：${error.message}`, true);
        await nextTick();
        this.scrollLog();
      } finally {
        this.sending = false;
      }
    },
    onPromptKeydown(event) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        this.submitPrompt();
      }
    },
    scrollLog() {
      const target = this.$refs.logRef;
      if (!target) {
        return;
      }
      target.scrollTop = target.scrollHeight;
    }
  }
}).mount("#app");
