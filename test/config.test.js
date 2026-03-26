const test = require("node:test");
const assert = require("node:assert/strict");
const { parseExtraArgs } = require("../src/config");

test("parseExtraArgs parses JSON arrays", () => {
  assert.deepEqual(parseExtraArgs('["--flag","value"]'), ["--flag", "value"]);
});

test("parseExtraArgs parses bracket shorthand arrays", () => {
  assert.deepEqual(parseExtraArgs("[--flag,value]"), ["--flag", "value"]);
});

test("parseExtraArgs preserves spaces for quoted bracket shorthand items", () => {
  assert.deepEqual(parseExtraArgs('["--flag","two words"]'), ["--flag", "two words"]);
});
