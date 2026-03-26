const { loadConfig } = require("./config");
const { GeminiCliClient } = require("./gemini-cli-client");
const { createAdapterServer } = require("./adapter-server");

function start() {
  const config = loadConfig();
  const geminiClient = new GeminiCliClient({
    command: config.geminiCommand,
    extraArgs: config.geminiExtraArgs,
    workdir: config.geminiWorkdir,
    timeoutMs: config.requestTimeoutMs
  });
  const { server } = createAdapterServer({
    config,
    geminiClient
  });

  server.on("error", (error) => {
    process.stderr.write(`[adapter] server error: ${error.message}\n`);
    process.exit(1);
  });

  server.listen(config.port, config.host, () => {
    const authState = config.apiKey ? "enabled" : "disabled";
    process.stdout.write(
      `[adapter] listening on http://${config.host}:${config.port} (auth ${authState})\n`
    );
    process.stdout.write(
      `[adapter] command: ${config.geminiCommand} ${config.geminiExtraArgs.join(" ")}\n`
    );
  });

  const close = () => {
    server.close(() => {
      process.exit(0);
    });
  };
  process.on("SIGINT", close);
  process.on("SIGTERM", close);
}

start();
