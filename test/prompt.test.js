const test = require("node:test");
const assert = require("node:assert/strict");
const { buildPromptFromMessages } = require("../src/prompt");

test("buildPromptFromMessages includes anti-tool and anti-preamble instructions", () => {
  const prompt = buildPromptFromMessages([{ role: "user", content: "你好" }]);

  assert.match(prompt, /Do not introduce yourself unless the user explicitly asked who you are\./);
  assert.match(prompt, /Do not mention Gemini CLI, tools, agents, delegation, approvals/);
  assert.match(prompt, /Do not use or describe tool calls\. Answer directly from the conversation\./);
});
