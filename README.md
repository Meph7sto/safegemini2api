# safegemini2api

本项目是一个本地适配器：支持直接以本地进程调用或通过 A2A (Agent-to-Agent) 分布式协议，将 Gemini CLI 封装为 OpenAI 兼容接口，方便 SillyTavern 等客户端无缝并安全地接入。

## 为什么本方案更安全？（与传统 OAuth 反代的本质区别）

在对接第三方客户端（如 SillyTavern）时，很多提供商会使用基于 OAuth 的云端反代服务。但使用那种传统反代方式极易**导致账号被封禁（封号）**，官方原文阐述如下：

Quick update to clear up some questions about recent changes.
We’ve gotten a lot of questions on using Gemini CLI outside of the terminal. You can continue to use Gemini CLI via officially supported protocols, specifically ACP and A2A, in a local or remote terminal, and in our Headless mode, including integrations utilizing the -p flag. 
You may not use Gemini CLI OAuth login screen to authenticate with a 3rd party application.

**本项目的不同之处（防封号核心）：**

本项目名副其实（**Safe**Gemini2API），本质上是一个**纯本地与官方合规工具的适配器**，完全规避了 OAuth 反代的封号危机：

- **完全合规的调用链路**：我们不涉及任何非官方的 Web 逆向或云端 OAuth 凭据劫持，而是**直接调用本机已合法安装配置的官方 Gemini CLI**。
- **纯本地网络身份**：请求的真正发起者是你自己电脑上的原生官方 CLI 客户端程序（处于你常用的干净本地 IP 环境）。从官方视角来看，你只是在一个正常的本地终端里高频使用了他们发布并允许使用的合法开发者工具，具有绝佳且天然的个人用户信誉度，完全不会触发数据中心批量调用的风控。
- **不存在凭据外泄**：一切环境变量和登录认证状态均保存在你本地，我们只是将 OpenAI API 格式的数据流转换成了官方允许的无头命令行参数（`-p` / `--output-format`）。

## 合规说明

- 本项目仅作为个人提效工具，通过本机 Gemini CLI 官方 Headless 接口完成任务。
- **坚决不提供** OAuth 借用、Token 提取、或云端共享登录态给第三方应用等高风险风控测试行为。
- 使用时仍请遵守目标模型服务方对应的账号/服务条款。

## 技术栈

- **前端**: Vue 3 + Vite（开发端口 5173）
- **后端**: Python FastAPI + Uvicorn（端口 8000）
- **通信**: RESTful API + SSE 流式传输

## 已实现能力

- `POST /v1/chat/completions`（非流式）
- `POST /v1/chat/completions`（`stream: true`，SSE）
- `GET /v1/models`
- `GET /healthz`
- 三种连接模式：`local_cli` / `local_a2a` / `remote_agent`
- 可选 Bearer 鉴权（设置 `OPENAI_API_KEY`）
- 并发限制、超时限制、错误映射
- Session 模式（增量消息传递）

## 运行前提

1. Python >= 3.10
2. [uv](https://docs.astral.sh/uv/) (Python 包管理)
3. Node.js >= 18
4. 已安装并可运行 Gemini CLI（例如 `gemini -p "hello"` 可用）
4. 你自己的 Gemini CLI 合法登录态/配置

## 快速启动

### 一键启动

Windows (CMD):

```bat
start.bat
```

Linux / macOS:

```bash
bash ./start.sh
```

脚本会自动：
1. `uv sync` 安装后端依赖（自动创建 venv）
2. 安装前端 npm 依赖
3. 启动本地 A2A Agent（10000）
4. 启动后端（8000）和前端（5173）

### 手动启动

后端：

```bash
uv sync --all-extras
uv run python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

访问：
- 本地 A2A Agent：`http://127.0.0.1:10000/agent-card`
- 前端界面：`http://127.0.0.1:5173`
- API 端点：`http://127.0.0.1:8000/v1/`

## 项目结构

```
safegemini2api/
├── backend/                # FastAPI 后端
│   ├── main.py             # 应用入口
│   ├── config.py           # 环境变量配置
│   ├── routers/            # API 路由
│   ├── services/           # Gemini CLI 客户端 + Prompt 构建
│   ├── models/             # Pydantic 数据模型
│   ├── middleware/         # 鉴权中间件
│   └── tests/              # pytest 测试
├── frontend/               # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── App.vue
│   │   ├── components/     # 组件
│   │   ├── composables/    # 逻辑复用
│   │   └── assets/         # 样式
│   ├── vite.config.js
│   └── package.json
├── .env.example            # 环境变量示例
├── .env                    # 环境变量（复制自 .env.example）
├── start.bat / start.sh    # 一键启动
└── README.md
```

## 关键环境变量

请将项目根目录下的 `.env.example` 复制一份并重命名为 `.env`，然后按需修改配置。主要配置说明如下：

```bash
# 服务
HOST=127.0.0.1
PORT=8000
OPENAI_API_KEY=your-local-key      # 可选，不设则不鉴权
DEFAULT_MODEL=gemini-2.5-flash
MAX_CONCURRENCY=4
REQUEST_TIMEOUT_MS=300000
MAX_BODY_BYTES=2097152

# 上下文模式
CONTEXT_MODE=stateless             # stateless 或 session
SESSION_KEY_HEADER=x-session-id
SESSION_KEY_FIELD=user

# Gemini CLI 调用
GEMINI_CLI_COMMAND=gemini
GEMINI_CLI_EXTRA_ARGS=["--approval-mode","plan"]
# GEMINI_WORKDIR=/path/to/workdir
```

`GEMINI_CLI_EXTRA_ARGS` 兼容两种格式：
- 标准 JSON 数组：`["--flag","value"]`
- 简写数组：`[--flag,value]`

## SillyTavern 配置示例

- API 类型：OpenAI 兼容
- Base URL：`http://127.0.0.1:8000/v1`
- API Key：与 `OPENAI_API_KEY` 保持一致（若服务端未设置可留空）
- Model：`gemini-2.5-flash`

前端里的连接模式说明：
- `local_cli`：后端直接调用本机 Gemini CLI
- `local_a2a`：后端通过本地 A2A Agent 调用本机 Gemini CLI
- `remote_agent`：后端通过远端 A2A Agent 转发请求

## 上下文模式说明

- `stateless`（默认）：每次都按 `messages` 全量构建 prompt，不依赖 CLI 会话。
- `session`：适配器会为同一会话键只转发"新增消息"，并在调用 Gemini CLI 时附加 `--resume`。

## 测试

```bash
uv run pytest -v
```

