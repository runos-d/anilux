import subprocess
import os
import sys
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import logging
from datetime import datetime

from django.core.cache import cache
from celery import current_app

from apps.anime.infrastructure.models.anime import Anime, Franchise
from apps.anime.application.tasks import run_kodik_import_task, rebuild_franchises_task

logger = logging.getLogger(__name__)


class RunKodikImportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        mode = request.data.get("mode", "update")
        limit = request.data.get("limit")
        try:
            limit_int = int(limit) if limit else None
        except (TypeError, ValueError):
            limit_int = None

        task = run_kodik_import_task.delay(mode=mode, limit=limit_int, download_posters=bool(request.data.get("download_posters", False)))
        cache.set(f"import_task:{task.id}", {
            "running": True,
            "finished": False,
            "success": None,
            "stopped": False,
            "log": "",
            "command": "import_from_kodik",
            "started": datetime.now().isoformat(),
            "task_id": task.id,
        }, timeout=3600)
        return Response({"success": True, "task_id": task.id})


class AdminImportStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        task_id = request.query_params.get("task_id")
        if task_id:
            state = cache.get(f"import_task:{task_id}")
            if state:
                return Response(state)
            try:
                result = current_app.AsyncResult(task_id)
                state = {
                    "running": result.status in ("PENDING", "STARTED", "RETRY"),
                    "finished": result.status in ("SUCCESS", "FAILURE", "REVOKED"),
                    "success": result.successful() if result.status == "SUCCESS" else None,
                    "stopped": result.status == "REVOKED",
                    "log": str(result.result) if result.status == "FAILURE" else "",
                    "command": "import_from_kodik",
                    "started": None,
                    "task_id": task_id,
                }
                return Response(state)
            except Exception:
                pass

        inspector = current_app.control.inspect()
        active = inspector.active() or {}
        for worker, tasks in active.items():
            for task in tasks:
                if "import" in task.get("name", ""):
                    return Response({
                        "running": True,
                        "finished": False,
                        "success": None,
                        "stopped": False,
                        "log": f"Task {task['id']} running on {worker}",
                        "command": task["name"],
                        "started": task.get("time"),
                        "task_id": task["id"],
                    })

        return Response({
            "running": False,
            "finished": True,
            "success": True,
            "stopped": False,
            "log": "",
            "command": None,
            "started": None,
        })


class AdminStopImportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        task_id = request.data.get("task_id")
        if task_id:
            try:
                current_app.control.revoke(task_id, terminate=True)
                cache.set(f"import_task:{task_id}", {
                    "running": False,
                    "finished": True,
                    "success": False,
                    "stopped": True,
                    "log": "Задача остановлена пользователем",
                    "command": "import_from_kodik",
                    "started": cache.get(f"import_task:{task_id}", {}).get("started"),
                }, timeout=3600)
                return Response({"stopped": True, "message": "Задача остановлена"})
            except Exception as e:
                return Response({"stopped": False, "error": str(e)}, status=500)
        return Response({"stopped": True, "message": "Нет активной задачи"})


class AdminRunFranchiseRebuildView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        dry_run = str(request.data.get("dry_run", "false")).lower() in ("true", "1", "yes")
        shikimori_ids = request.data.get("shikimori_ids")
        if shikimori_ids is None:
            shikimori_ids = []
        elif isinstance(shikimori_ids, (int, str)):
            shikimori_ids = [int(shikimori_ids)]
        else:
            shikimori_ids = [int(x) for x in shikimori_ids]

        if not shikimori_ids:
            anime_qs = Anime.objects.filter(shikimori_id__isnull=False).exclude(shikimori_id=0)
            shikimori_ids = list(anime_qs.values_list("shikimori_id", flat=True))

        task = rebuild_franchises_task.delay(shikimori_ids=shikimori_ids, dry_run=dry_run)
        cache.set(f"import_task:{task.id}", {
            "running": True,
            "finished": False,
            "success": None,
            "stopped": False,
            "log": "",
            "command": "rebuild_franchises",
            "started": datetime.now().isoformat(),
            "task_id": task.id,
        }, timeout=3600)
        return Response({"success": True, "task_id": task.id, "count": len(shikimori_ids)})


class AdminRunCalendarSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({
            "success": True,
            "log": "Функция синхронизации календаря не реализована",
            "returncode": 0,
        })


class AdminWipeAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        targets = request.data.get("targets", [])
        anime_deleted = 0
        franchises_deleted = 0
        if "anime" in targets:
            anime_deleted = Anime.objects.count()
            Anime.objects.all().delete()
        if "franchises" in targets:
            franchises_deleted = Franchise.objects.count()
            Franchise.objects.all().delete()
        return Response({
            "success": True,
            "anime_deleted": anime_deleted,
            "franchises_deleted": franchises_deleted,
        })


class RunJikanImportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        script_path = request.data.get("script_path", "").strip()
        if not script_path:
            return Response({"error": "Не указан путь к скрипту"}, status=400)

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        if not os.path.abspath(script_path).startswith(project_root):
            return Response({"error": "Недопустимый путь к скрипту"}, status=400)

        if not os.path.exists(script_path):
            return Response({"error": f"Файл не найден: {script_path}"}, status=400)

        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=180,
            )

            log = result.stdout
            if result.stderr:
                log += "\nSTDERR:\n" + result.stderr

            return Response(
                {
                    "success": result.returncode == 0,
                    "log": log,
                    "returncode": result.returncode,
                }
            )

        except subprocess.TimeoutExpired:
            return Response(
                {"error": "Обновление превысило время ожидания (3 мин)"}, status=500
            )
        except Exception as e:
            return Response({"error": str(e)}, status=500)

