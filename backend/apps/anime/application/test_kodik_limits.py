from types import SimpleNamespace

from django.core.cache import cache
from django.test import RequestFactory, SimpleTestCase, override_settings

from apps.anime.application.kodik_limits import KodikLimitExceeded, reserve_unique_ids


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class KodikLimitTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.request = RequestFactory().post("/")
        self.request.user = SimpleNamespace(is_authenticated=True, pk=7)

    def test_duplicate_ids_only_consume_one_slot(self):
        reserve_unique_ids(self.request, [1, 1, 1])
        reserve_unique_ids(self.request, range(1, 101))
        with self.assertRaises(KodikLimitExceeded):
            reserve_unique_ids(self.request, [101])
