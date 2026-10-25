from django.core.management import call_command
from django.db import connection, transaction
from django.test.runner import DiscoverRunner


class DisposableSeoRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        assert connection.settings_dict['HOST'] == 'anilux-seo-mysql'
        assert connection.settings_dict['NAME'] == 'seo_acceptance'
        call_command('migrate', interactive=False, verbosity=0)
        from django.contrib.auth import get_user_model
        from .models import SiteSeoSettings, SeoAlias, SeoHub, SeoOverride, SeoCollection
        from apps.anime.infrastructure.models.anime import Anime, Franchise, Genre
        self.baseline = transaction.atomic()
        self.baseline.__enter__()
        for model in [get_user_model(), Anime, Franchise, Genre, SiteSeoSettings, SeoAlias, SeoHub, SeoOverride, SeoCollection]:
            model.objects.all().delete()
        return []

    def teardown_databases(self, old_config, **kwargs):
        transaction.set_rollback(True)
        self.baseline.__exit__(None, None, None)
