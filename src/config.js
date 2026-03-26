const path = require("path");

function parseIntEnv(name, defaultValue) {
  const raw = process.env[name];
  if (!raw) {
    return defaultValue;
  }
  const value = Number.parseInt(raw, 10);
  return Number.isFinite(value) && value > 0 ? value : defaultValue;
}

function parseExtraArgs(raw) {
  if (!raw) {
    return [];
  }
  const trimmed = raw.trim();
  try {
    const parsed = JSON.parse(trimmed);
    if (Array.isArray(parsed)) {
      return parsed.map(String);
    }
  } catch (_) {
    // Fall through to whitespace split.
  }

  if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
    const items = [];
    const inner = trimmed.slice(1, -1).trim();
    let current = "";
    let quote = "";

    for (const char of inner) {
      if (quote) {
        if (char === quote) {
          quote = "";
        } else {
          current += char;
        }
        continue;
      }

      if (char === '"' || char === "'") {
        quote = char;
        continue;
      }

      if (char === ",") {
        const value = current.trim();
        if (value) {
          items.push(value);
        }
        current = "";
        continue;
      }

      current += char;
    }

    const last = current.trim();
    if (last) {
      items.push(last);
    }

    return items;
  }

  return trimmed
    .split(/\s+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function loadConfig() {
  const host = process.env.HOST || "127.0.0.1";
  const port = parseIntEnv("PORT", 3000);
  const maxConcurrency = parseIntEnv("MAX_CONCURRENCY", 4);
  const requestTimeoutMs = parseIntEnv("REQUEST_TIMEOUT_MS", 120000);
  const maxBodyBytes = parseIntEnv("MAX_BODY_BYTES", 2 * 1024 * 1024);
  const contextModeRaw = (process.env.CONTEXT_MODE || "stateless").toLowerCase();
  const contextMode = contextModeRaw === "session" ? "session" : "stateless";

  return {
    host,
    port,
    apiKey: process.env.OPENAI_API_KEY || "",
    defaultModel: process.env.DEFAULT_MODEL || "gemini-2.5-flash",
    geminiCommand: process.env.GEMINI_CLI_COMMAND || "gemini",
    geminiExtraArgs: parseExtraArgs(process.env.GEMINI_CLI_EXTRA_ARGS || ""),
    geminiWorkdir: process.env.GEMINI_WORKDIR
      ? path.resolve(process.env.GEMINI_WORKDIR)
      : process.cwd(),
    contextMode,
    sessionKeyHeader: (process.env.SESSION_KEY_HEADER || "x-session-id").toLowerCase(),
    sessionKeyField: process.env.SESSION_KEY_FIELD || "user",
    maxConcurrency,
    requestTimeoutMs,
    maxBodyBytes
  };
}

module.exports = {
  loadConfig,
  parseExtraArgs
};
