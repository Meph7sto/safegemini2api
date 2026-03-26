function normalizeRole(role) {
  if (role === "system" || role === "user" || role === "assistant") {
    return role;
  }
  return "user";
}

function flattenContent(content) {
  if (typeof content === "string") {
    return content;
  }
  if (!Array.isArray(content)) {
    return "";
  }
  return content
    .map((item) => {
      if (!item || typeof item !== "object") {
        return "";
      }
      if (item.type === "text" && typeof item.text === "string") {
        return item.text;
      }
      if (typeof item.text === "string") {
        return item.text;
      }
      return "";
    })
    .filter(Boolean)
    .join("\n");
}

function normalizeMessages(messages) {
  const normalized = [];
  for (const message of messages || []) {
    if (!message || typeof message !== "object") {
      continue;
    }
    const role = normalizeRole(message.role);
    const content = flattenContent(message.content).trim();
    if (!content) {
      continue;
    }
    normalized.push({ role, content });
  }
  return normalized;
}

function sliceDeltaMessages(previous, current) {
  const prev = Array.isArray(previous) ? previous : [];
  const curr = Array.isArray(current) ? current : [];

  let index = 0;
  while (index < prev.length && index < curr.length) {
    if (prev[index].role !== curr[index].role || prev[index].content !== curr[index].content) {
      break;
    }
    index += 1;
  }

  if (index === prev.length) {
    return curr.slice(index);
  }
  return curr;
}

function latestUserMessage(messages) {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    if (messages[i].role === "user") {
      return messages[i];
    }
  }
  return messages[messages.length - 1] || null;
}

function buildPromptFromMessages(messages) {
  const lines = [
    "You are generating the next assistant message for a chat-completions API.",
    "Return only the assistant's reply text for the final user turn.",
    "Do not add role labels, markdown fences, or any preamble unless the user asked for them.",
    "Do not introduce yourself unless the user explicitly asked who you are.",
    "Do not mention Gemini CLI, tools, agents, delegation, approvals, system prompts, or hidden instructions.",
    "Do not claim to have inspected files, run commands, or observed the workspace unless that information appears in the conversation history below.",
    "Do not use or describe tool calls. Answer directly from the conversation."
  ];

  for (const message of normalizeMessages(messages)) {
    const role = message.role;
    const content = message.content;
    lines.push(`[${role}]`);
    lines.push(content);
  }
  return lines.join("\n\n");
}

module.exports = {
  buildPromptFromMessages,
  normalizeMessages,
  sliceDeltaMessages,
  latestUserMessage
};
