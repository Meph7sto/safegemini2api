# safegemini2api

本项目是一个本地适配器：把 Gemini CLI（官方允许的 Headless `-p` 调用）封装为 OpenAI 兼容接口，方便 SillyTavern 等客户端接入。

## 技术栈

- **前端**: Vue 3 + Vite（开发端口 5173）
- **后端**: Python FastAPI + Uvicorn（端口 8000）
- **通信**: RESTful API + SSE 流式传输

## 已实现能力

- `POST /v1/chat/completions`（非流式）
- `POST /v1/chat/completions`（`stream: true`，SSE）
- `GET /v1/models`
- `GET /healthz`
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
3. 同时启动后端（8000）和前端（5173）

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
├── .env                    # 环境变量
├── start.bat / start.sh    # 一键启动
└── README.md
```

## 关键环境变量

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

## 上下文模式说明

- `stateless`（默认）：每次都按 `messages` 全量构建 prompt，不依赖 CLI 会话。
- `session`：适配器会为同一会话键只转发"新增消息"，并在调用 Gemini CLI 时附加 `--resume`。

## 测试

```bash
uv run pytest -v
```

## 合规说明

- 本项目仅通过本机 Gemini CLI 官方 Headless 接口调用（`-p` + `--output-format`）。
- 不提供 OAuth 借用、共享登录态给第三方应用等高风险能力。
- 使用时请遵守 Gemini CLI 和对应账号/服务条款。
