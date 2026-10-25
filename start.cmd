@echo off
setlocal
cd /d "%~dp0"

if not exist ".env" (
  echo [ERROR] .env is missing. Run setup.cmd first.
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo [ERROR] Frontend dependencies are missing. Run setup.cmd first.
  exit /b 1
)

echo [START] Starting MySQL, Redis, Mailpit, migrations, backend and workers...
docker compose up -d mysql redis mailpit migrate backend celery_worker celery_beat native_builder || exit /b 1

echo [START] Starting frontend at http://localhost:5173 ...
call npm run dev --prefix "frontend"
