const { spawn } = require("child_process");

class GeminiCliError extends Error {
  constructor(message, details = {}) {
    super(message);
    this.name = "GeminiCliError";
    this.details = details;
  }
}

function safeJsonParse(text) {
  try {
    return JSON.parse(text);
  } catch (_) {
    return null;
  }
}

function extractText(node) {
  if (!node) {
    return "";
  }
  if (typeof node === "string") {
    return node;
  }
  if (Array.isArray(node)) {
    return node.map(extractText).filter(Boolean).join("");
  }
  if (typeof node === "object") {
    if (typeof node.text === "string") {
      return node.text;
    }
    if (typeof node.content === "string") {
      return node.content;
    }
    if (Array.isArray(node.content)) {
      return node.content.map(extractText).filter(Boolean).join("");
    }
    if (Array.isArray(node.parts)) {
      return node.parts.map(extractText).filter(Boolean).join("");
    }
    if (typeof node.response === "string") {
      return node.response;
    }
  }
  return "";
}

function shouldUseAssistantPayload(event, role) {
  if (!role) {
    return true;
  }
  const lower = String(role).toLowerCase();
  return lower === "assistant" || lower === "model";
}

function extractAssistantTextFromStreamEvent(event) {
  if (!event || typeof event !== "object") {
    return "";
  }

  const type = String(event.type || event.event || "").toLowerCase();
  const message = event.message || event.data || event.delta || event.result || event;
  const role = message.role || event.role;

  if (type && type !== "message" && type !== "result" && type !== "output_text_delta") {
    return "";
  }
  if (!shouldUseAssistantPayload(event, role)) {
    return "";
  }

  return (
    extractText(message) ||
    extractText(event.response) ||
    extractText(event.content) ||
    ""
  );
}

function diffChunk(previous, next) {
  if (!next) {
    return { snapshot: previous, delta: "" };
  }
  if (!previous) {
    return { snapshot: next, delta: next };
  }
  if (next.startsWith(previous)) {
    return { snapshot: next, delta: next.slice(previous.length) };
  }
  if (previous.endsWith(next)) {
    return { snapshot: previous, delta: "" };
  }
  return { snapshot: previous + next, delta: next };
}

function withTimeout(signal, timeoutMs) {
  const controller = new AbortController();
  let timeoutId = null;

  const onAbort = () => controller.abort(signal.reason || new Error("Aborted"));
  if (signal) {
    if (signal.aborted) {
      onAbort();
    } else {
      signal.addEventListener("abort", onAbort, { once: true });
    }
  }

  if (timeoutMs > 0) {
    timeoutId = setTimeout(() => {
      controller.abort(new Error(`Gemini CLI timed out after ${timeoutMs}ms`));
    }, timeoutMs);
  }

  return {
    signal: controller.signal,
    cleanup: () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      if (signal) {
        signal.removeEventListener("abort", onAbort);
      }
    }
  };
}

class GeminiCliClient {
  constructor(options) {
    this.command = options.command;
    this.extraArgs = options.extraArgs || [];
    this.workdir = options.workdir || process.cwd();
    this.timeoutMs = options.timeoutMs || 120000;
  }

  getBaseArgs() {
    const args = [...this.extraArgs];
    const hasApprovalMode = args.includes("--approval-mode");
    const hasYolo = args.includes("--yolo") || args.includes("-y");

    if (!hasApprovalMode && !hasYolo) {
      args.push("--approval-mode", "plan");
    }

    return args;
  }

  buildArgs({ prompt, model, outputFormat, resume, sessionId }) {
    const args = this.getBaseArgs();
    if (resume) {
      args.push("--resume");
      if (sessionId) {
        args.push(String(sessionId));
      }
    }
    if (model) {
      args.push("-m", model);
    }
    args.push("-p", prompt);
    if (outputFormat) {
      args.push("--output-format", outputFormat);
    }
    return args;
  }

  async generate({ prompt, model, signal, timeoutMs, resume, sessionId }) {
    const args = this.buildArgs({
      prompt,
      model,
      outputFormat: "json",
      resume,
      sessionId
    });
    const result = await this.runCommand({
      args,
      signal,
      timeoutMs: timeoutMs || this.timeoutMs
    });

    const trimmed = result.stdout.trim();
    const payload = safeJsonParse(trimmed);

    if (payload && payload.error) {
      throw new GeminiCliError(payload.error.message || "Gemini CLI returned an error", {
        payload,
        stderr: result.stderr
      });
    }

    const text =
      (payload && extractText(payload.response || payload.result || payload.message)) ||
      trimmed;

    if (!text) {
      throw new GeminiCliError("Gemini CLI returned empty output", {
        stdout: result.stdout,
        stderr: result.stderr
      });
    }

    return {
      text,
      raw: payload || trimmed,
      stderr: result.stderr
    };
  }

  async streamGenerate({ prompt, model, onText, signal, timeoutMs, resume, sessionId }) {
    const args = this.buildArgs({
      prompt,
      model,
      outputFormat: "stream-json",
      resume,
      sessionId
    });

    let snapshot = "";
    let fullText = "";
    let lineBuffer = "";

    const flushLine = (line) => {
      const trimmed = line.trim();
      if (!trimmed) {
        return;
      }
      const payload = safeJsonParse(trimmed);
      if (!payload) {
        return;
      }
      const candidate = extractAssistantTextFromStreamEvent(payload);
      if (!candidate) {
        return;
      }
      const diff = diffChunk(snapshot, candidate);
      snapshot = diff.snapshot;
      if (!diff.delta) {
        return;
      }
      fullText += diff.delta;
      if (typeof onText === "function") {
        onText(diff.delta);
      }
    };

    await this.runCommand({
      args,
      signal,
      timeoutMs: timeoutMs || this.timeoutMs,
      onStdout: (chunk) => {
        lineBuffer += chunk;
        const lines = lineBuffer.split("\n");
        lineBuffer = lines.pop() || "";
        for (const line of lines) {
          flushLine(line);
        }
      }
    });

    if (lineBuffer.trim()) {
      flushLine(lineBuffer);
    }

    return { text: fullText };
  }

  runCommand({ args, signal, timeoutMs, onStdout }) {
    const control = withTimeout(signal, timeoutMs);
    return new Promise((resolve, reject) => {
      const child = spawn(this.command, args, {
        cwd: this.workdir,
        stdio: ["ignore", "pipe", "pipe"],
        signal: control.signal,
        env: process.env
      });

      let stdout = "";
      let stderr = "";
      let settled = false;

      const finalize = (fn, value) => {
        if (settled) {
          return;
        }
        settled = true;
        control.cleanup();
        fn(value);
      };

      child.stdout.setEncoding("utf8");
      child.stderr.setEncoding("utf8");

      child.stdout.on("data", (chunk) => {
        stdout += chunk;
        if (onStdout) {
          onStdout(chunk);
        }
      });
      child.stderr.on("data", (chunk) => {
        stderr += chunk;
      });
      child.on("error", (error) => {
        finalize(reject, new GeminiCliError(`Failed to run Gemini CLI: ${error.message}`, { error }));
      });

      child.on("close", (code, termSignal) => {
        if (code === 0) {
          finalize(resolve, { stdout, stderr });
          return;
        }
        const message = control.signal.aborted
          ? control.signal.reason?.message || "Gemini CLI aborted"
          : `Gemini CLI exited with code ${code}${termSignal ? ` (${termSignal})` : ""}`;
        finalize(
          reject,
          new GeminiCliError(message, {
            code,
            signal: termSignal,
            stdout,
            stderr
          })
        );
      });
    });
  }
}

module.exports = {
  GeminiCliClient,
  GeminiCliError
};
