@echo off
setlocal
cd /d "%~dp0"

where node >nul 2>nul || (echo [ERROR] Node.js was not found in PATH. & exit /b 1)
where npm >nul 2>nul || (echo [ERROR] npm was not found in PATH. & exit /b 1)
where docker >nul 2>nul || (echo [ERROR] Docker was not found in PATH. & exit /b 1)
docker compose version >nul 2>nul || (echo [ERROR] Docker Compose is unavailable. & exit /b 1)

if not exist ".env" (
  copy /Y ".env.example" ".env" >nul || exit /b 1
  echo [OK] Created .env from .env.example.
) else (
  echo [OK] Existing .env was preserved.
)

echo [SETUP] Installing locked frontend dependencies...
call npm ci --prefix "frontend" || exit /b 1

echo [SETUP] Pulling service images...
docker compose pull mysql redis mailpit || exit /b 1

echo [SETUP] Building application images...
docker compose build migrate backend celery_worker celery_beat native_builder || exit /b 1

echo [OK] Setup complete. Run start.cmd.
