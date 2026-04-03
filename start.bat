@echo off
setlocal EnableExtensions EnableDelayedExpansion

pushd "%~dp0" >nul 2>nul
if errorlevel 1 (
  echo [start] Error: failed to enter project directory.
  echo [start] Path: %~dp0
  goto :fail
)
set "ROOT_DIR=%~dp0"

if /I "%~1" NEQ "__run__" (
  start "safegemini2api-launcher" cmd /k ""%~f0" __run__"
  exit /b 0
 )

title safegemini2api launcher

:: ── Stop any existing services ──
call "%~dp0stop.bat"

:: ── Check uv ──
where uv >nul 2>nul
if errorlevel 1 (
  echo [start] Error: uv is not installed or not in PATH.
  echo [start] Install: https://docs.astral.sh/uv/getting-started/installation/
  goto :fail
)

:: ── Check Node.js ──
where node >nul 2>nul
if errorlevel 1 (
  echo [start] Error: Node.js is not installed or not in PATH.
  goto :fail
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [start] Error: npm is not installed or not in PATH.
  goto :fail
)

node -e "const [major, minor] = process.versions.node.split('.').map(Number); const ok = (major === 20 && minor >= 19) || (major === 22 && minor >= 12) || major > 22; process.exit(ok ? 0 : 1)"
if errorlevel 1 (
  echo [start] Error: Node.js version is incompatible with Vite 8.
  echo [start] Detected:
  node -p "process.versions.node"
  echo [start] Required: 20.19+ or 22.12+
  goto :fail
)

:: ── Backend setup ──
echo [start] Syncing backend dependencies (uv)...
uv sync --all-extras
if errorlevel 1 (
  echo [start] Error: backend dependency sync failed.
  goto :fail
)

:: ── Frontend setup ──
if not exist "frontend\node_modules" (
  echo [start] Installing frontend dependencies...
  cd frontend
  call npm install
  if errorlevel 1 (
    echo [start] Error: frontend dependency install failed.
    goto :fail
  )
  cd ..
)

set "ROLLDOWN_BINDING="
for /f "usebackq delims=" %%i in (`node -e "const p=process.platform; const a=process.arch; if (p==='linux' && a==='x64') console.log('@rolldown/binding-linux-x64-gnu'); else if (p==='linux' && a==='arm64') console.log('@rolldown/binding-linux-arm64-gnu'); else if (p==='win32' && a==='x64') console.log('@rolldown/binding-win32-x64-msvc'); else if (p==='win32' && a==='arm64') console.log('@rolldown/binding-win32-arm64-msvc'); else if (p==='darwin' && a==='x64') console.log('@rolldown/binding-darwin-x64'); else if (p==='darwin' && a==='arm64') console.log('@rolldown/binding-darwin-arm64');"`) do set "ROLLDOWN_BINDING=%%i"
set "ROLLDOWN_BINDING_FILE="
for /f "usebackq delims=" %%i in (`node -e "const p=process.platform; const a=process.arch; let file=''; if (p==='linux'&&a==='x64') file='frontend/node_modules/@rolldown/binding-linux-x64-gnu/rolldown-binding.linux-x64-gnu.node'; else if (p==='linux'&&a==='arm64') file='frontend/node_modules/@rolldown/binding-linux-arm64-gnu/rolldown-binding.linux-arm64-gnu.node'; else if (p==='win32'&&a==='x64') file='frontend/node_modules/@rolldown/binding-win32-x64-msvc/rolldown-binding.win32-x64-msvc.node'; else if (p==='win32'&&a==='arm64') file='frontend/node_modules/@rolldown/binding-win32-arm64-msvc/rolldown-binding.win32-arm64-msvc.node'; else if (p==='darwin'&&a==='x64') file='frontend/node_modules/@rolldown/binding-darwin-x64/rolldown-binding.darwin-x64.node'; else if (p==='darwin'&&a==='arm64') file='frontend/node_modules/@rolldown/binding-darwin-arm64/rolldown-binding.darwin-arm64.node'; console.log(file);"`) do set "ROLLDOWN_BINDING_FILE=%%i"

if defined ROLLDOWN_BINDING_FILE (
  if not exist "%ROLLDOWN_BINDING_FILE%" (
    echo [start] Missing optional Vite native binding (%ROLLDOWN_BINDING%^); repairing frontend dependencies...
    cd frontend
    call npm install
    if errorlevel 1 (
      echo [start] Error: frontend dependency repair failed.
      goto :fail
    )
    cd ..
  )
  )
)

if defined ROLLDOWN_BINDING_FILE (
  if not exist "%ROLLDOWN_BINDING_FILE%" (
    echo [start] Error: Vite native binding is still missing after npm install.
    echo [start] Try: rmdir /s /q frontend\node_modules ^& del frontend\package-lock.json ^& cd frontend ^& npm install
    goto :fail
  )
)

:: ── Start both servers ──
echo.
echo [start] Starting local A2A agent on port 10000...
start "safegemini2api-a2a" cmd /k "pushd ""%ROOT_DIR%"" && uv run python -m uvicorn backend.services.local_a2a_agent:app --host 127.0.0.1 --port 10000 --reload"

echo [start] Starting backend (FastAPI) on port 8000...
start "safegemini2api-backend" cmd /k "pushd ""%ROOT_DIR%"" && uv run python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

echo [start] Starting frontend (Vite) on port 5173...
start "safegemini2api-frontend" cmd /k "pushd ""%ROOT_DIR%frontend"" && npm run dev"

echo.
echo ================================================
echo   Local A2A: http://127.0.0.1:10000/agent-card
echo   Backend:  http://127.0.0.1:8000
echo   Frontend: http://127.0.0.1:5173
echo   API:      http://127.0.0.1:8000/v1/
echo ================================================
echo.
echo Press any key to stop both servers...
pause >nul

:: ── Cleanup ──
taskkill /FI "WINDOWTITLE eq safegemini2api-a2a" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq safegemini2api-backend" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq safegemini2api-frontend" /T /F >nul 2>nul
popd >nul 2>nul
echo [start] Servers stopped.
exit /b 0

:fail
echo.
popd >nul 2>nul
echo [start] Startup aborted. Press any key to close this window...
pause >nul
exit /b 1
