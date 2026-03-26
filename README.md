# safegemini2api

本项目是一个本地适配器：把 Gemini CLI（官方允许的 Headless `-p` 调用）封装为 OpenAI 兼容接口，方便 SillyTavern 接入。

## 已实现能力

- `POST /v1/chat/completions`（非流式）
- `POST /v1/chat/completions`（`stream: true`，SSE）
- `GET /v1/models`
- `GET /healthz`
- 可选 Bearer 鉴权（设置 `OPENAI_API_KEY`）
- 并发限制、超时限制、错误映射

## 运行前提

1. Node.js >= 18
2. 已安装并可运行 Gemini CLI（例如 `gemini -p "hello"` 可用）
3. 你自己的 Gemini CLI 合法登录态/配置（本项目不绕过官方认证流程）

## 快速启动

Linux / macOS:

```bash
bash ./start.sh
```

Windows (CMD):

```bat
start.bat
```

默认监听：`http://127.0.0.1:3000`
（一键脚本默认以 dev 模式启动，支持代码变更自动重启）

启动脚本会按平台分别加载环境变量：

- `start.sh`：先读 `.env`，再读 `.env.linux`
- `start.bat`：先读 `.env`，再读 `.env.windows`

注意：`GEMINI_CLI_COMMAND`、`GEMINI_CLI_EXTRA_ARGS`、`GEMINI_WORKDIR` 这三个变量现在只从平台文件读取，`.env` 中即使设置了也会被忽略。这样可以避免 WSL 误继承 Windows 的 `powershell.exe` 配置。

前端调试界面：`http://127.0.0.1:3000/ui/`
（使用 Vue 3，本地运行时文件由 `node_modules/vue/dist/vue.global.prod.js` 提供）

## 关键环境变量

```bash
# 服务
HOST=127.0.0.1
PORT=3000
OPENAI_API_KEY=your-local-key      # 可选，不设则不鉴权
DEFAULT_MODEL=gemini-2.5-flash
MAX_CONCURRENCY=4
REQUEST_TIMEOUT_MS=120000
MAX_BODY_BYTES=2097152
CONTEXT_MODE=stateless             # stateless 或 session
SESSION_KEY_HEADER=x-session-id    # session 模式下优先从请求头取会话键
SESSION_KEY_FIELD=user             # 其次从请求体字段取会话键

# Gemini CLI 调用
GEMINI_CLI_COMMAND=gemini
GEMINI_CLI_EXTRA_ARGS='[--approval-mode,plan]'  # 默认建议 read-only，session 模式会自动附加 --resume
GEMINI_WORKDIR=/path/to/workdir     # 可选
```

建议把共用配置放进 `.env`，把平台相关的 Gemini CLI 配置放进各自文件。

`.env.linux`:

```bash
GEMINI_CLI_COMMAND=gemini
GEMINI_CLI_EXTRA_ARGS=[--approval-mode,plan]
```

`.env.windows`:

```bat
GEMINI_CLI_COMMAND=gemini
GEMINI_CLI_EXTRA_ARGS=[--approval-mode,plan]
```

如果你在 Windows 下确实要显式调用 PowerShell 包装脚本，也可以这样写：

```bat
GEMINI_CLI_COMMAND=powershell.exe
GEMINI_CLI_EXTRA_ARGS=[-NoProfile,-ExecutionPolicy,Bypass,-File,C:\Users\ASUS\AppData\Roaming\npm\gemini.ps1,--approval-mode,yolo]
```

`GEMINI_CLI_EXTRA_ARGS` 现在兼容两种格式：

- 标准 JSON 数组：`["--flag","value"]`
- 简写数组：`[--flag,value]`

如果你希望适配器更像传统聊天接口，建议保留默认的 `--approval-mode plan`，避免 Gemini CLI 在 headless 模式下进入 agent/tool loop。

## SillyTavern 配置示例

- API 类型：OpenAI 兼容
- Base URL：`http://127.0.0.1:3000/v1`
- API Key：与 `OPENAI_API_KEY` 保持一致（若服务端未设置可留空）
- Model：`gemini-2.5-flash`（或你在请求中指定的模型）

## 上下文模式说明

- `stateless`（默认）：每次都按 `messages` 全量构建 prompt，不依赖 CLI 会话。
- `session`：适配器会为同一会话键只转发“新增消息”，并在调用 Gemini CLI 时附加 `--resume`（可减少酒馆重复发送全历史导致的重复上下文问题）。

建议在 `session` 模式下为每个聊天传稳定会话键（请求头 `x-session-id` 或请求体 `user`），避免不同聊天串到同一 CLI 会话。

## 测试

```bash
npm test
```

测试覆盖：

- Gemini CLI 客户端（JSON/stream-json 解析、失败路径）
- OpenAI 兼容接口（非流式/流式/鉴权）

## 合规说明

- 本项目仅通过本机 Gemini CLI 官方 Headless 接口调用（`-p` + `--output-format`）。
- 不提供 OAuth 借用、共享登录态给第三方应用等高风险能力。
- 使用时请遵守 Gemini CLI 和对应账号/服务条款。
