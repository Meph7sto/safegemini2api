@echo off
setlocal EnableExtensions

pushd "%~dp0" >nul 2>nul
if errorlevel 1 (
  echo [stop] Error: failed to enter project directory.
  goto :fail
)

echo [stop] Stopping safegemini2api services...

taskkill /FI "WINDOWTITLE eq safegemini2api-a2a" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq safegemini2api-backend" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq safegemini2api-frontend" /T /F >nul 2>nul

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :10000 ^| findstr LISTENING') do (
  taskkill /PID %%a /T /F >nul 2>nul
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
  taskkill /PID %%a /T /F >nul 2>nul
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
  taskkill /PID %%a /T /F >nul 2>nul
)

echo [stop] Done.
popd >nul 2>nul
exit /b 0

:fail
popd >nul 2>nul
exit /b 1
