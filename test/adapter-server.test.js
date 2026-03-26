const test = require("node:test");
const assert = require("node:assert/strict");
const { once } = require("node:events");
const { PassThrough } = require("node:stream");
const { createRequestHandler } = require("../src/adapter-server");

function createMockReq({ method, url, headers, body }) {
  const req = new PassThrough();
  req.method = method;
  req.url = url;
  req.headers = { host: "localhost", ...(headers || {}) };
  process.nextTick(() => {
    if (body) {
      req.write(body);
    }
    req.end();
  });
  return req;
}

function createMockRes() {
  const res = new PassThrough();
  res.statusCode = 200;
  res.headers = {};
  res.headersSent = false;
  res.body = "";

  res.writeHead = function writeHead(statusCode, headers = {}) {
    this.statusCode = statusCode;
    this.headers = { ...headers };
    this.headersSent = true;
    return this;
  };

  const rawWrite = res.write.bind(res);
  res.write = function write(chunk, encoding, callback) {
    if (chunk) {
      this.body += Buffer.isBuffer(chunk) ? chunk.toString("utf8") : String(chunk);
    }
    this.headersSent = true;
    return rawWrite(chunk, encoding, callback);
  };

  const rawEnd = res.end.bind(res);
  res.end = function end(chunk, encoding, callback) {
    if (chunk) {
      this.body += Buffer.isBuffer(chunk) ? chunk.toString("utf8") : String(chunk);
    }
    this.headersSent = true;
    return rawEnd(chunk, encoding, callback);
  };

  return res;
}

async function invoke(handler, reqOptions) {
  const req = createMockReq(reqOptions);
  const res = createMockRes();
  const completed = once(res, "finish");
  handler(req, res);
  await completed;
  return {
    statusCode: res.statusCode,
    headers: res.headers,
    body: res.body
  };
}

function createConfig(overrides = {}) {
  return {
    apiKey: "",
    defaultModel: "gemini-2.5-flash",
    maxConcurrency: 2,
    requestTimeoutMs: 1000,
    maxBodyBytes: 1024 * 1024,
    ...overrides
  };
}

test("POST /v1/chat/completions returns OpenAI-compatible non-stream response", async () => {
  const handler = createRequestHandler({
    config: createConfig({ apiKey: "test-key" }),
    geminiClient: {
      async generate() {
        return { text: "hello from gemini" };
      },
      async streamGenerate() {
        throw new Error("should not be called");
      }
    },
    logger: { error() {} }
  });

  const response = await invoke(handler, {
    method: "POST",
    url: "/v1/chat/completions",
    headers: {
      authorization: "Bearer test-key",
      "content-type": "application/json"
    },
    body: JSON.stringify({
      model: "gemini-2.5-flash",
      stream: false,
      messages: [{ role: "user", content: "hi" }]
    })
  });

  const json = JSON.parse(response.body);
  assert.equal(response.statusCode, 200);
  assert.equal(json.object, "chat.completion");
  assert.equal(json.choices[0].message.content, "hello from gemini");
});

test("POST /v1/chat/completions stream returns SSE chunks and [DONE]", async () => {
  const handler = createRequestHandler({
    config: createConfig(),
    geminiClient: {
      async generate() {
        throw new Error("should not be called");
      },
      async streamGenerate({ onText }) {
        onText("hello");
        onText(" world");
        return { text: "hello world" };
      }
    },
    logger: { error() {} }
  });

  const response = await invoke(handler, {
    method: "POST",
    url: "/v1/chat/completions",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      stream: true,
      messages: [{ role: "user", content: "hi" }]
    })
  });

  assert.equal(response.statusCode, 200);
  assert.match(response.body, /chat\.completion\.chunk/);
  assert.match(response.body, /"content":"hello"/);
  assert.match(response.body, /\[DONE\]/);
});

test("auth is enforced when OPENAI_API_KEY is configured", async () => {
  const handler = createRequestHandler({
    config: createConfig({ apiKey: "must-auth" }),
    geminiClient: {
      async generate() {
        return { text: "unused" };
      },
      async streamGenerate() {
        return { text: "unused" };
      }
    },
    logger: { error() {} }
  });

  const response = await invoke(handler, {
    method: "POST",
    url: "/v1/chat/completions",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      stream: false,
      messages: [{ role: "user", content: "hi" }]
    })
  });

  const json = JSON.parse(response.body);
  assert.equal(response.statusCode, 401);
  assert.equal(json.error.type, "authentication_error");
});

test("GET /ui serves the frontend page", async () => {
  const handler = createRequestHandler({
    config: createConfig(),
    geminiClient: {
      async generate() {
        return { text: "unused" };
      },
      async streamGenerate() {
        return { text: "unused" };
      }
    },
    logger: { error() {} }
  });

  const response = await invoke(handler, {
    method: "GET",
    url: "/ui/",
    headers: {}
  });

  assert.equal(response.statusCode, 200);
  assert.match(response.body, /Gemini Adapter Console/);
});

test("session mode forwards only incremental turns and enables resume", async () => {
  const calls = [];
  const handler = createRequestHandler({
    config: createConfig({
      contextMode: "session",
      sessionKeyHeader: "x-session-id",
      sessionKeyField: "user"
    }),
    geminiClient: {
      async generate(input) {
        calls.push(input);
        return { text: "ok" };
      },
      async streamGenerate() {
        throw new Error("should not be called");
      }
    },
    logger: { error() {} }
  });

  await invoke(handler, {
    method: "POST",
    url: "/v1/chat/completions",
    headers: {
      "content-type": "application/json",
      "x-session-id": "chat-a"
    },
    body: JSON.stringify({
      stream: false,
      messages: [{ role: "user", content: "你好，先自我介绍" }]
    })
  });

  await invoke(handler, {
    method: "POST",
    url: "/v1/chat/completions",
    headers: {
      "content-type": "application/json",
      "x-session-id": "chat-a"
    },
    body: JSON.stringify({
      stream: false,
      messages: [
        { role: "user", content: "你好，先自我介绍" },
        { role: "assistant", content: "我是 Gemini 助手。" },
        { role: "user", content: "继续，讲三点能力" }
      ]
    })
  });

  assert.equal(calls.length, 2);
  assert.equal(calls[0].resume, true);
  assert.equal(calls[0].sessionId, "chat-a");
  assert.match(calls[0].prompt, /先自我介绍/);

  assert.equal(calls[1].resume, true);
  assert.equal(calls[1].sessionId, "chat-a");
  assert.doesNotMatch(calls[1].prompt, /我是 Gemini 助手/);
  assert.match(calls[1].prompt, /继续，讲三点能力/);
});
