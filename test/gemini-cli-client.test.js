const test = require("node:test");
const assert = require("node:assert/strict");
const { GeminiCliClient, GeminiCliError } = require("../src/gemini-cli-client");

function createClient() {
  return new GeminiCliClient({
    command: "gemini",
    extraArgs: [],
    workdir: process.cwd(),
    timeoutMs: 2000
  });
}

test("GeminiCliClient.generate returns parsed response text", async () => {
  const client = createClient();
  client.runCommand = async () => ({
    stdout: JSON.stringify({
      response: "Echo: hello world",
      stats: { inputTokens: 10, outputTokens: 20 }
    }),
    stderr: ""
  });

  const result = await client.generate({
    prompt: "hello world",
    model: "gemini-test"
  });
  assert.equal(result.text, "Echo: hello world");
});

test("GeminiCliClient.streamGenerate emits assistant deltas", async () => {
  const client = createClient();
  client.runCommand = async ({ onStdout }) => {
    onStdout(
      `${JSON.stringify({
        type: "message",
        message: { role: "assistant", content: "Echo:" }
      })}\n`
    );
    onStdout(
      `${JSON.stringify({
        type: "message",
        message: { role: "assistant", content: "Echo: stream me" }
      })}\n`
    );
    onStdout(`${JSON.stringify({ type: "result", response: "Echo: stream me" })}\n`);
    return { stdout: "", stderr: "" };
  };

  const chunks = [];
  const result = await client.streamGenerate({
    prompt: "stream me",
    model: "gemini-test",
    onText: (delta) => chunks.push(delta)
  });

  assert.equal(result.text, "Echo: stream me");
  assert.equal(chunks.join(""), "Echo: stream me");
});

test("GeminiCliClient.generate throws on CLI payload error", async () => {
  const client = createClient();
  client.runCommand = async () => ({
    stdout: JSON.stringify({
      error: { message: "mock failure" }
    }),
    stderr: "mock failure"
  });

  await assert.rejects(
    () =>
      client.generate({
        prompt: "__FAIL__",
        model: "gemini-test"
      }),
    (error) => error instanceof GeminiCliError
  );
});

test("GeminiCliClient.buildArgs adds resume flags when requested", async () => {
  const client = createClient();
  const args = client.buildArgs({
    prompt: "hi",
    model: "gemini-test",
    outputFormat: "json",
    resume: true,
    sessionId: "chat-1"
  });

  assert.deepEqual(args, [
    "--approval-mode",
    "plan",
    "--resume",
    "chat-1",
    "-m",
    "gemini-test",
    "-p",
    "hi",
    "--output-format",
    "json"
  ]);
});

test("GeminiCliClient.buildArgs does not overwrite explicit approval mode", async () => {
  const client = new GeminiCliClient({
    command: "gemini",
    extraArgs: ["--approval-mode", "yolo"],
    workdir: process.cwd(),
    timeoutMs: 2000
  });

  const args = client.buildArgs({
    prompt: "hi",
    model: "gemini-test",
    outputFormat: "json"
  });

  assert.deepEqual(args, [
    "--approval-mode",
    "yolo",
    "-m",
    "gemini-test",
    "-p",
    "hi",
    "--output-format",
    "json"
  ]);
});
