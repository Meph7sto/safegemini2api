#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

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

# ── Start both servers ──
cleanup() {
  echo ""
  echo "[start] Stopping servers..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  echo "[start] Done."
}
trap cleanup EXIT INT TERM

echo ""
echo "[start] Starting backend (FastAPI) on port 8000..."
uv run python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

echo "[start] Starting frontend (Vite) on port 5173..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "================================================"
echo "  Backend:  http://127.0.0.1:8000"
echo "  Frontend: http://127.0.0.1:5173"
echo "  API:      http://127.0.0.1:8000/v1/"
echo "================================================"
echo ""

wait
