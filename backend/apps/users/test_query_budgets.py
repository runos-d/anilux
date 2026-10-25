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

    @patch("core.online_status.online_status.get_online_users", return_value=[])
    def test_user_list_query_count_does_not_grow_with_page_size(self, _online):
        request = APIRequestFactory().get("/api/users/users/?page_size=30")
        force_authenticate(request, self.viewer)
        with self.assertNumQueries(2):
            response = UsersListView.as_view()(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data["results"]), 30)
