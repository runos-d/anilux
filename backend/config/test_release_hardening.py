from django.test import RequestFactory, SimpleTestCase, tag

from config.middleware import ReleaseFeatureGateMiddleware


@tag("release-gates")
class DisabledFeatureRoutesTests(SimpleTestCase):
    def test_disabled_feature_routes_are_404_without_database_access(self):
        paths = (
            "/api/dubs/",
            "/api/dubs/groups/",
            "/api/reactor/posts/",
            "/api/users/2fa/status/",
            "/api/users/verify/phone/",
            "/api/studios/sync/",
            "/api/studios/example/discussions/00000000-0000-0000-0000-000000000000/like/",
        )
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path, HTTP_AUTHORIZATION="Bearer deliberately.invalid")
                self.assertEqual(response.status_code, 404)

    def test_debug_routes_are_not_mounted_when_debug_is_false(self):
        for path in ("/api/users/headers-debug/", "/api/users/auth-debug/"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_middleware_guard_short_circuits_before_view_work(self):
        called = False

        def downstream(_request):
            nonlocal called
            called = True
            raise AssertionError("disabled feature reached its view")

        response = ReleaseFeatureGateMiddleware(downstream)(
            RequestFactory().get("/api/reactor/posts/")
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(called)
