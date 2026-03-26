@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

call :load_env ".env"
set "GEMINI_CLI_COMMAND="
set "GEMINI_CLI_EXTRA_ARGS="
set "GEMINI_WORKDIR="
call :load_env ".env.windows"

if not defined GEMINI_CLI_COMMAND set "GEMINI_CLI_COMMAND=gemini"
if not defined GEMINI_CLI_EXTRA_ARGS set "GEMINI_CLI_EXTRA_ARGS=[--approval-mode,plan]"

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

where "%GEMINI_CLI_COMMAND%" >nul 2>nul
if errorlevel 1 (
  echo [start] Error: Gemini CLI command "%GEMINI_CLI_COMMAND%" is not installed or not in PATH.
  echo [start] Please verify: %GEMINI_CLI_COMMAND% -p "hello"
  exit /b 1
)

node -e "require.resolve('vue/package.json')" >nul 2>nul
if errorlevel 1 (
  echo [start] dependencies missing, installing...
  call npm install
  if errorlevel 1 exit /b 1
)

echo [start] Starting safegemini2api in dev mode...
call npm run dev
exit /b %errorlevel%

:load_env
if exist "%~1" (
  echo [start] Loading environment from %~1
  for /f "usebackq tokens=* delims=" %%L in ("%~1") do (
    set "line=%%L"
    if not "!line!"=="" if not "!line:~0,1!"=="#" (
      for /f "tokens=1,* delims==" %%A in ("!line!") do (
        if not "%%A"=="" set "%%A=%%B"
      )
    )
  )
)
exit /b 0
