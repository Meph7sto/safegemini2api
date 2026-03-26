const http = require("http");
const fs = require("fs/promises");
const path = require("path");
const { URL } = require("url");
const {
  newChatId,
  newChunk,
  newCompletion,
  makeError
} = require("./openai");
const {
  buildPromptFromMessages,
  normalizeMessages,
  sliceDeltaMessages,
  latestUserMessage
} = require("./prompt");
const { GeminiCliError } = require("./gemini-cli-client");
const UI_DIR = path.resolve(__dirname, "..", "ui");
const VUE_RUNTIME_PATH = path.resolve(
  __dirname,
  "..",
  "node_modules",
  "vue",
  "dist",
  "vue.global.prod.js"
);

function sendJson(res, statusCode, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(statusCode, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(body)
  });
  res.end(body);
}

function sendText(res, statusCode, contentType, text) {
  res.writeHead(statusCode, {
    "content-type": `${contentType}; charset=utf-8`,
    "content-length": Buffer.byteLength(text)
  });
  res.end(text);
}

async function serveStaticFile(res, absolutePath, contentType) {
  try {
    const content = await fs.readFile(absolutePath);
    res.writeHead(200, {
      "content-type": `${contentType}; charset=utf-8`,
      "content-length": content.length
    });
    res.end(content);
  } catch (_) {
    sendText(res, 404, "text/plain", "Not found");
  }
}

async function serveUiFile(res, fileName, contentType) {
  await serveStaticFile(res, path.join(UI_DIR, fileName), contentType);
}

function writeSse(res, payload) {
  res.write(`data: ${JSON.stringify(payload)}\n\n`);
}

function sendDone(res) {
  res.write("data: [DONE]\n\n");
  res.end();
}

function readJsonBody(req, maxBodyBytes) {
  return new Promise((resolve, reject) => {
    let size = 0;
    let body = "";
    req.setEncoding("utf8");
    req.on("data", (chunk) => {
      size += Buffer.byteLength(chunk);
      if (size > maxBodyBytes) {
        reject(new Error(`Request body exceeds ${maxBodyBytes} bytes`));
        req.destroy();
        return;
      }
      body += chunk;
    });
    req.on("end", () => {
      try {
        const parsed = body ? JSON.parse(body) : {};
        resolve(parsed);
      } catch (error) {
        reject(new Error("Invalid JSON body"));
      }
    });
    req.on("error", reject);
  });
}

function validateChatCompletionBody(body) {
  if (!body || typeof body !== "object") {
    throw new Error("Body must be a JSON object");
  }
  if (!Array.isArray(body.messages) || body.messages.length === 0) {
    throw new Error("`messages` must be a non-empty array");
  }
  for (const message of body.messages) {
    if (!message || typeof message !== "object") {
      throw new Error("Each message must be an object");
    }
    if (typeof message.role !== "string") {
      throw new Error("Each message requires a string `role`");
    }
  }
  if (body.model && typeof body.model !== "string") {
    throw new Error("`model` must be a string");
  }
  return {
    messages: body.messages,
    model: body.model || "",
    stream: Boolean(body.stream)
  };
}

function authFailed(req, apiKey) {
  if (!apiKey) {
    return false;
  }
  const auth = req.headers.authorization || "";
  const expected = `Bearer ${apiKey}`;
  return auth !== expected;
}

function pickHeader(req, headerName) {
  if (!headerName) {
    return "";
  }
  const value = req.headers[String(headerName).toLowerCase()];
  if (typeof value === "string") {
    return value.trim();
  }
  if (Array.isArray(value) && value.length > 0) {
    return String(value[0] || "").trim();
  }
  return "";
}

function resolveSessionKey(req, body, config) {
  const fromHeader = pickHeader(req, config.sessionKeyHeader || "x-session-id");
  if (fromHeader) {
    return fromHeader;
  }
  const field = config.sessionKeyField || "user";
  const fromBody = body && typeof body[field] === "string" ? body[field].trim() : "";
  if (fromBody) {
    return fromBody;
  }
  return "default";
}

function mapError(err) {
  if (err instanceof GeminiCliError) {
    const msg = err.message || "Gemini CLI execution failed";
    if (msg.toLowerCase().includes("timed out")) {
      return {
        status: 504,
        payload: makeError({
          type: "api_timeout_error",
          message: msg
        })
      };
    }
    return {
      status: 502,
      payload: makeError({
        type: "api_error",
        message: msg
      })
    };
  }
  return {
    status: 500,
    payload: makeError({
      type: "server_error",
      message: err && err.message ? err.message : "Internal server error"
    })
  };
}

function createRequestHandler({ config, geminiClient, logger = console }) {
  let inFlight = 0;
  const sessionStates = new Map();

  return async (req, res) => {
    const parsedUrl = new URL(req.url, `http://${req.headers.host || "localhost"}`);

    if (req.method === "GET" && parsedUrl.pathname === "/") {
      res.writeHead(302, { location: "/ui/" });
      res.end();
      return;
    }

    if (req.method === "GET" && (parsedUrl.pathname === "/ui" || parsedUrl.pathname === "/ui/")) {
      await serveUiFile(res, "index.html", "text/html");
      return;
    }

    if (req.method === "GET" && parsedUrl.pathname === "/ui/styles.css") {
      await serveUiFile(res, "styles.css", "text/css");
      return;
    }

    if (req.method === "GET" && parsedUrl.pathname === "/ui/app.js") {
      await serveUiFile(res, "app.js", "application/javascript");
      return;
    }

    if (req.method === "GET" && parsedUrl.pathname === "/ui/vendor/vue.global.prod.js") {
      await serveStaticFile(res, VUE_RUNTIME_PATH, "application/javascript");
      return;
    }

    if (req.method === "GET" && parsedUrl.pathname === "/healthz") {
      sendJson(res, 200, { ok: true });
      return;
    }

    if (req.method === "GET" && parsedUrl.pathname === "/v1/models") {
      sendJson(res, 200, {
        object: "list",
        data: [
          {
            id: config.defaultModel,
            object: "model",
            owned_by: "google-gemini-cli"
          }
        ]
      });
      return;
    }

    if (req.method !== "POST" || parsedUrl.pathname !== "/v1/chat/completions") {
      sendJson(
        res,
        404,
        makeError({
          type: "invalid_request_error",
          message: "Route not found"
        })
      );
      return;
    }

    if (authFailed(req, config.apiKey)) {
      sendJson(
        res,
        401,
        makeError({
          type: "authentication_error",
          message: "Invalid or missing API key"
        })
      );
      return;
    }

    if (inFlight >= config.maxConcurrency) {
      sendJson(
        res,
        429,
        makeError({
          type: "rate_limit_error",
          message: "Server is busy, retry later"
        })
      );
      return;
    }

    let body;
    try {
      body = await readJsonBody(req, config.maxBodyBytes);
    } catch (error) {
      sendJson(
        res,
        400,
        makeError({
          type: "invalid_request_error",
          message: error.message
        })
      );
      return;
    }

    let params;
    try {
      params = validateChatCompletionBody(body);
    } catch (error) {
      sendJson(
        res,
        400,
        makeError({
          type: "invalid_request_error",
          message: error.message
        })
      );
      return;
    }

    inFlight += 1;
    const model = params.model || config.defaultModel;
    const normalizedMessages = normalizeMessages(params.messages);
    let promptMessages = normalizedMessages;
    let resume = false;
    let sessionId = "";
    let shouldPersistSessionState = false;

    if (config.contextMode === "session") {
      resume = true;
      sessionId = resolveSessionKey(req, body, config);
      const previousMessages = sessionStates.get(sessionId) || [];
      const deltaMessages = sliceDeltaMessages(previousMessages, normalizedMessages);
      promptMessages = deltaMessages.length > 0 ? [...deltaMessages] : [];
      while (promptMessages.length > 0 && promptMessages[0].role === "assistant") {
        promptMessages.shift();
      }
      if (promptMessages.length === 0) {
        const latest = latestUserMessage(normalizedMessages);
        if (latest) {
          promptMessages = [latest];
        } else {
          promptMessages = normalizedMessages;
        }
      }
      shouldPersistSessionState = true;
    }

    const prompt = buildPromptFromMessages(promptMessages);
    const id = newChatId();
    const controller = new AbortController();
    req.on("aborted", () => controller.abort(new Error("Client disconnected")));

    try {
      if (!params.stream) {
        const result = await geminiClient.generate({
          prompt,
          model,
          signal: controller.signal,
          timeoutMs: config.requestTimeoutMs,
          resume,
          sessionId
        });
        sendJson(
          res,
          200,
          newCompletion({
            id,
            model,
            content: result.text
          })
        );
        if (shouldPersistSessionState) {
          sessionStates.set(sessionId, normalizedMessages);
        }
        return;
      }

      res.writeHead(200, {
        "content-type": "text/event-stream; charset=utf-8",
        "cache-control": "no-cache, no-transform",
        connection: "keep-alive"
      });

      writeSse(
        res,
        newChunk({
          id,
          model,
          delta: { role: "assistant" },
          finishReason: null
        })
      );

      await geminiClient.streamGenerate({
        prompt,
        model,
        signal: controller.signal,
        timeoutMs: config.requestTimeoutMs,
        resume,
        sessionId,
        onText: (delta) => {
          if (!delta) {
            return;
          }
          writeSse(
            res,
            newChunk({
              id,
              model,
              delta: { content: delta },
              finishReason: null
            })
          );
        }
      });

      writeSse(
        res,
        newChunk({
          id,
          model,
          delta: {},
          finishReason: "stop"
        })
      );
      sendDone(res);
      if (shouldPersistSessionState) {
        sessionStates.set(sessionId, normalizedMessages);
      }
    } catch (error) {
      logger.error("[adapter] request failed:", error);
      const mapped = mapError(error);
      if (!res.headersSent) {
        sendJson(res, mapped.status, mapped.payload);
        return;
      }
      writeSse(res, mapped.payload);
      sendDone(res);
    } finally {
      inFlight -= 1;
    }
  };
}

function createAdapterServer({ config, geminiClient, logger = console }) {
  const handler = createRequestHandler({ config, geminiClient, logger });
  const server = http.createServer(handler);
  return { server };
}

module.exports = {
  createAdapterServer,
  createRequestHandler,
  validateChatCompletionBody,
  authFailed,
  readJsonBody
};
