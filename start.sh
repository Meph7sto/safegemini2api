#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

load_env_file() {
  local file="$1"
  if [[ -f "${file}" ]]; then
    echo "[start] Loading environment from ${file}"
    set -a
    # shellcheck disable=SC1090
    source "${file}"
    set +a
  fi
}

if ! command -v node >/dev/null 2>&1; then
  echo "[start] Error: Node.js is not installed or not in PATH."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[start] Error: npm is not installed or not in PATH."
  exit 1
fi

load_env_file ".env"
unset GEMINI_CLI_COMMAND GEMINI_CLI_EXTRA_ARGS GEMINI_WORKDIR
load_env_file ".env.linux"

export GEMINI_CLI_COMMAND="${GEMINI_CLI_COMMAND:-gemini}"
export GEMINI_CLI_EXTRA_ARGS="${GEMINI_CLI_EXTRA_ARGS:-[--approval-mode,plan]}"

if ! command -v "${GEMINI_CLI_COMMAND}" >/dev/null 2>&1; then
  echo "[start] Error: Gemini CLI command '${GEMINI_CLI_COMMAND}' is not installed or not in PATH."
  echo "[start] Please verify: ${GEMINI_CLI_COMMAND} -p \"hello\""
  exit 1
fi

if ! node -e "require.resolve('vue/package.json')" >/dev/null 2>&1; then
  echo "[start] dependencies missing, installing..."
  npm install
fi

echo "[start] Starting safegemini2api in dev mode..."
exec npm run dev
