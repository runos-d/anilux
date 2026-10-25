---
id: F0002
title: Общий корень настроек и fallback Django
status: active
date: '2026-10-11'
tags:
- environment
- build
kind: environmental
governed-by: D0002
---

Compose задаёт env_file `.env`, Vite envDir указывает корень проекта и читает VITE_*. Django ищет ENV_FILE, затем корневой `.env`, затем исторический серверный путь и fallback load_dotenv(); README описывает единый корневой файл как намерение.

Источники: `docker-compose.yml`, `frontend/vite.config.ts`, `backend/config/settings.py`, `README.md`.
