from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.users.infrastructure.models.users import Subscription, User, UserProfileSettings
from apps.users.presentation.views.users_views import UsersListView


class UserListQueryBudgetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.viewer = User.objects.create_user(
            username="viewer", email="viewer@example.com", password="Safe-pass-1842"
        )
        for index in range(30):
            user = User.objects.create_user(
                username=f"person-{index}",
                email=f"person-{index}@example.com",
                password="Safe-pass-1842",
            )
            Subscription.objects.get_or_create(user=user)
            UserProfileSettings.objects.get_or_create(user=user)

    @patch("core.online_status.online_status.get_users_data", return_value={})
    def test_user_list_query_count_does_not_grow_with_page_size(self, _online):
        request = APIRequestFactory().get("/api/users/users/?page_size=30")
        force_authenticate(request, self.viewer)
        with self.assertNumQueries(2):
            response = UsersListView.as_view()(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data["results"]), 30)

    @patch("core.online_status.online_status.get_users_data", return_value={})
    def test_contact_privacy_adds_one_batched_query(self, _online):
        from apps.users.infrastructure.models.users import PrivacySettings
        from django.utils import timezone
        for user in User.objects.filter(username__startswith="person-"):
            PrivacySettings.objects.update_or_create(user=user, defaults={"who_can_see_last_seen": "contacts"})
        User.objects.filter(username__startswith="person-").update(last_login=timezone.now())
        for size in (1, 30):
            request = APIRequestFactory().get(f"/api/users/users/?page_size={size}")
            force_authenticate(request, self.viewer)
            with self.assertNumQueries(3):
                response = UsersListView.as_view()(request)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(all(row["last_login"] is None for row in response.data["results"]))

    @patch("core.online_status.online_status.get_users_data", return_value={})
    def test_hidden_presence_cannot_be_inferred_from_directory_tabs(self, _online):
        from apps.users.infrastructure.models.users import UserSettings
        hidden = User.objects.get(username="person-0")
        UserSettings.objects.update_or_create(user=hidden, defaults={"show_online_status": False})
        with patch("core.online_status.online_status.get_online_ids", return_value=[hidden.pk]):
            for tab, present in (("online", False), ("offline", True)):
                request = APIRequestFactory().get(f"/api/users/users/?tab={tab}&search=person-0")
                force_authenticate(request, self.viewer)
                response = UsersListView.as_view()(request)
                self.assertEqual(any(row["id"] == hidden.pk for row in response.data["results"]), present)
