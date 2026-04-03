# Local A2A Agent

This document describes the Local A2A Agent architecture and usage.

## Overview

The SafeGemini2 API supports three connection modes:

| Mode | Description | Agent URL |
|------|-------------|-----------|
| **Local CLI** | Direct Gemini CLI invocation | N/A |
| **Local A2A** | Local A2A Agent service on port 10000 | `http://localhost:10000` |
| **Remote Agent** | Remote A2A-compatible agent | User-specified URL |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        Frontend                          │
│  [Local CLI] [Local A2A] [Remote Agent]  ← Mode Buttons  │
│  Agent URL input (only for Remote Agent mode)           │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                     Backend API                          │
│  POST /v1/chat/completions                               │
│  Body: { connection_mode, agent_url, messages, ... }    │
│                                                         │
│  connection_mode detection:                              │
│  - "local_cli"      → GeminiCliClient (direct CLI)       │
│  - "local_a2a"     → A2AClient → localhost:10000        │
│  - "remote_agent"  → A2AClient → user-specified URL     │
└─────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┴───────────────────┐
          ▼                   ▼                   ▼
    [gemini CLI]      [Local A2A Agent]      [Remote A2A]
    (subprocess)       (port 10000)         (user URL)
                           │
                           ▼
                    [gemini CLI]
                    (subprocess)
```

## Local A2A Agent Service

The Local A2A Agent is a service that exposes the Gemini CLI via the A2A (Agent-to-Agent) protocol.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/agent-card` | Returns A2A Agent Card JSON |
| GET | `/.well-known/agent-card.json` | Returns A2A Agent Card JSON |
| POST | `/` | Handles A2A JSON-RPC requests |

### Agent Card

```json
{
  "protocolVersion": "0.3.0",
  "name": "local-gemini-cli-agent",
  "version": "1.0.0",
  "description": "Local A2A agent that wraps Gemini CLI",
  "url": "http://localhost:10000",
  "preferredTransport": "JSONRPC",
  "capabilities": {
    "streaming": true
  },
  "defaultInputModes": ["text/plain"],
  "defaultOutputModes": ["text/plain", "application/json"]
}
```

### Starting the Agent

```bash
# Terminal 1: Start the Local A2A Agent
python -m backend.start_a2a_agent

# Or run directly with uvicorn
uvicorn backend.services.local_a2a_agent:app --host 0.0.0.0 --port 10000
```

### A2A JSON-RPC Protocol

The agent accepts JSON-RPC 2.0 requests:

```json
{
  "jsonrpc": "2.0",
  "id": "req-1",
  "method": "message/send",
  "params": {
    "message": {
      "kind": "message",
      "messageId": "msg-1",
      "role": "user",
      "parts": [
        {
          "kind": "text",
          "text": "Your prompt here"
        }
      ]
    },
    "metadata": {
      "model": "gemini-2.5-flash",
      "resume": false,
      "session_id": ""
    }
  }
}
```

Streaming requests use `message/stream` and return `text/event-stream`.

Each SSE event contains a JSON-RPC response in its `data:` field:

```json
{
  "jsonrpc": "2.0",
  "id": "req-1",
  "result": {
    "kind": "message",
    "messageId": "agent-msg-1",
    "role": "agent",
    "contextId": "ctx-1",
    "parts": [
      {
        "kind": "text",
        "text": "streaming delta text"
      }
    ]
  }
}
```

## Launch Sequence

When using Local A2A mode, `start.sh` / `start.bat` already start the local agent automatically.

If you want to run services manually, start them in this order:

```bash
# Terminal 1: Start Local A2A Agent
python -m backend.start_a2a_agent

# Terminal 2: Start Backend API
python -m backend.main

# Terminal 3: Start Frontend
cd frontend && npm run dev
```

## Request Format

### Backend Request (POST /v1/chat/completions)

```json
{
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "model": "gemini-2.5-flash",
  "stream": true,
  "connection_mode": "local_a2a",
  "agent_url": "http://localhost:10000"
}
```

For `local_a2a` mode, the `agent_url` is optional (defaults to `http://localhost:10000`).

For `remote_agent` mode, `agent_url` is required.

## Differences Between Modes

| Aspect | Local CLI | Local A2A | Remote Agent |
|--------|-----------|----------|--------------|
| Latency | Lowest | Low | Depends on network |
| Resource usage | Single process | Service + CLI | Depends on remote |
| Streaming | Yes (stream-json) | Yes (SSE) | Yes (SSE) |
| Setup | None | Start agent service | None |
| Use case | Development | Local agent testing | Production/CI/CD |
