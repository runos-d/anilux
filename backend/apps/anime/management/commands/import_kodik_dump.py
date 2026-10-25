import json

from django.core.management.base import BaseCommand

from apps.anime.application import kodik_dump_service


class Command(BaseCommand):
    help = "Импорт каталога и календаря из дампов Kodik (dumps.kodikres.com)"

    def add_arguments(self, parser):
        parser.add_argument("--only", choices=["catalog", "calendar", "all"], default="all")
        parser.add_argument("--force", action="store_true", help="скачать и обработать, даже если дамп не менялся")
        parser.add_argument("--dry-run", action="store_true", help="только посчитать изменения каталога, ничего не писать в БД")
        parser.add_argument("--max-new", type=int, default=3000, help="максимум новых тайтлов за запуск")

    def handle(self, *args, **options):
        result = {}
        if options["only"] in ("catalog", "all"):
            result["catalog"] = kodik_dump_service.sync_catalog(
                force=options["force"], max_new=options["max_new"], dry_run=options["dry_run"])
        if options["only"] in ("calendar", "all"):
            result["calendar"] = kodik_dump_service.sync_calendar(force=options["force"])
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))