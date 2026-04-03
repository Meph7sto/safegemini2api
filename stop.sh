#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

echo "[stop] Stopping safegemini2api services..."

pkill -f "uvicorn backend.main:app" 2>/dev/null || true
pkill -f "uvicorn backend.services.local_a2a_agent:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

lsof -ti:10000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

echo "[stop] Done."
