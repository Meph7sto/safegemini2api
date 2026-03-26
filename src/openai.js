const crypto = require("crypto");

function nowUnix() {
  return Math.floor(Date.now() / 1000);
}

function newChatId() {
  return `chatcmpl-${crypto.randomUUID().replace(/-/g, "")}`;
}

function newCompletion({
  id,
  model,
  content,
  finishReason = "stop",
  promptTokens = 0,
  completionTokens = 0
}) {
  return {
    id,
    object: "chat.completion",
    created: nowUnix(),
    model,
    choices: [
      {
        index: 0,
        message: {
          role: "assistant",
          content
        },
        finish_reason: finishReason
      }
    ],
    usage: {
      prompt_tokens: promptTokens,
      completion_tokens: completionTokens,
      total_tokens: promptTokens + completionTokens
    }
  };
}

function newChunk({ id, model, delta, finishReason = null }) {
  return {
    id,
    object: "chat.completion.chunk",
    created: nowUnix(),
    model,
    choices: [
      {
        index: 0,
        delta,
        finish_reason: finishReason
      }
    ]
  };
}

function makeError({ message, type = "invalid_request_error", code }) {
  return {
    error: {
      message,
      type,
      code: code || type
    }
  };
}

module.exports = {
  newChatId,
  newCompletion,
  newChunk,
  makeError
};
