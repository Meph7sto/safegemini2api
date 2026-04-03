#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

# ── Stop any existing services ──
bash "${ROOT_DIR}/stop.sh"

# ── Check uv ──
if ! command -v uv >/dev/null 2>&1; then
  echo "[start] Error: uv is not installed or not in PATH."
  echo "[start] Install: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

# ── Check Node.js ──
if ! command -v node >/dev/null 2>&1; then
  echo "[start] Error: Node.js is not installed or not in PATH."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[start] Error: npm is not installed or not in PATH."
  exit 1
fi

# ── Backend setup ──
echo "[start] Syncing backend dependencies (uv)..."
uv sync --all-extras

# ── Frontend setup ──
if [ ! -d "frontend/node_modules" ]; then
  echo "[start] Installing frontend dependencies..."
  (cd frontend && npm install)
fi

ROLLDOWN_BINDING="$(node -e "const p=process.platform; const a=process.arch; if (p==='linux' && a==='x64') console.log('@rolldown/binding-linux-x64-gnu'); else if (p==='linux' && a==='arm64') console.log('@rolldown/binding-linux-arm64-gnu'); else if (p==='win32' && a==='x64') console.log('@rolldown/binding-win32-x64-msvc'); else if (p==='win32' && a==='arm64') console.log('@rolldown/binding-win32-arm64-msvc'); else if (p==='darwin' && a==='x64') console.log('@rolldown/binding-darwin-x64'); else if (p==='darwin' && a==='arm64') console.log('@rolldown/binding-darwin-arm64');")"
ROLLDOWN_BINDING_FILE="$(node -e "const p=process.platform; const a=process.arch; let file=''; if (p==='linux'&&a==='x64') file='frontend/node_modules/@rolldown/binding-linux-x64-gnu/rolldown-binding.linux-x64-gnu.node'; else if (p==='linux'&&a==='arm64') file='frontend/node_modules/@rolldown/binding-linux-arm64-gnu/rolldown-binding.linux-arm64-gnu.node'; else if (p==='win32'&&a==='x64') file='frontend/node_modules/@rolldown/binding-win32-x64-msvc/rolldown-binding.win32-x64-msvc.node'; else if (p==='win32'&&a==='arm64') file='frontend/node_modules/@rolldown/binding-win32-arm64-msvc/rolldown-binding.win32-arm64-msvc.node'; else if (p==='darwin'&&a==='x64') file='frontend/node_modules/@rolldown/binding-darwin-x64/rolldown-binding.darwin-x64.node'; else if (p==='darwin'&&a==='arm64') file='frontend/node_modules/@rolldown/binding-darwin-arm64/rolldown-binding.darwin-arm64.node'; console.log(file)")"
if [ -n "${ROLLDOWN_BINDING_FILE}" ] && [ ! -f "${ROLLDOWN_BINDING_FILE}" ]; then
  echo "[start] Missing optional Vite native binding (${ROLLDOWN_BINDING}); repairing frontend dependencies..."
  (cd frontend && npm install)
fi

if [ -n "${ROLLDOWN_BINDING_FILE}" ] && [ ! -f "${ROLLDOWN_BINDING_FILE}" ]; then
  echo "[start] Error: Vite native binding is still missing after npm install."
  echo "[start] Try: rm -rf frontend/node_modules frontend/package-lock.json && cd frontend && npm install"
  exit 1
fi

# ── Start both servers ──
cleanup() {
  echo ""
  echo "[start] Stopping servers..."
  kill "$A2A_PID" "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$A2A_PID" "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  echo "[start] Done."
}
trap cleanup EXIT INT TERM

echo ""
echo "[start] Starting local A2A agent on port 10000..."
uv run python -m uvicorn backend.services.local_a2a_agent:app --host 127.0.0.1 --port 10000 --reload &
A2A_PID=$!

echo "[start] Starting backend (FastAPI) on port 8000..."
uv run python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

echo "[start] Starting frontend (Vite) on port 5173..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "================================================"
echo "  Local A2A: http://127.0.0.1:10000/agent-card"
echo "  Backend:  http://127.0.0.1:8000"
echo "  Frontend: http://127.0.0.1:5173"
echo "  API:      http://127.0.0.1:8000/v1/"
echo "================================================"
echo ""

wait
