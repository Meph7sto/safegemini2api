@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

:: ── Check uv ──
where uv >nul 2>nul
if errorlevel 1 (
  echo [start] Error: uv is not installed or not in PATH.
  echo [start] Install: https://docs.astral.sh/uv/getting-started/installation/
  exit /b 1
)

:: ── Check Node.js ──
where node >nul 2>nul
if errorlevel 1 (
  echo [start] Error: Node.js is not installed or not in PATH.
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [start] Error: npm is not installed or not in PATH.
  exit /b 1
)

:: ── Backend setup ──
echo [start] Syncing backend dependencies (uv)...
uv sync --all-extras
if errorlevel 1 exit /b 1

:: ── Frontend setup ──
if not exist "frontend\node_modules" (
  echo [start] Installing frontend dependencies...
  cd frontend
  call npm install
  if errorlevel 1 exit /b 1
  cd ..
)

:: ── Start both servers ──
echo.
echo [start] Starting backend (FastAPI) on port 8000...
start "safegemini2api-backend" cmd /c "cd /d %~dp0 && uv run python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

echo [start] Starting frontend (Vite) on port 5173...
start "safegemini2api-frontend" cmd /c "cd /d %~dp0\frontend && npm run dev"

echo.
echo ================================================
echo   Backend:  http://127.0.0.1:8000
echo   Frontend: http://127.0.0.1:5173
echo   API:      http://127.0.0.1:8000/v1/
echo ================================================
echo.
echo Press any key to stop both servers...
pause >nul

:: ── Cleanup ──
taskkill /FI "WINDOWTITLE eq safegemini2api-backend" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq safegemini2api-frontend" /T /F >nul 2>nul
echo [start] Servers stopped.
