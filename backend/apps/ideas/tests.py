from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Idea


class IdeaApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="idea-author",
            email="idea-author@example.com",
            password="strong-test-password",
        )
        self.admin = user_model.objects.create_user(
            username="idea-admin",
            email="idea-admin@example.com",
            password="strong-test-password",
            is_staff=True,
        )
        self.idea = Idea.objects.create(
            author=self.user,
            title="Удобный список обновлений",
            description="Показывать изменения проекта в одном удобном месте.",
        )

    def test_board_is_public_and_creation_starts_pending(self):
        response = self.client.get(reverse("idea-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("idea-list"),
            {
                "title": "Добавить быстрый поиск",
                "description": "Нужен поиск по сохранённым идеям и сообщениям.",
                "kind": Idea.Kind.IMPROVEMENT,
                "status": Idea.Status.DONE,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Idea.Status.PENDING)

    def test_only_staff_can_move_an_idea(self):
        detail_url = reverse("idea-detail", args=[self.idea.id])
        self.client.force_authenticate(self.user)
        response = self.client.patch(detail_url, {"status": Idea.Status.IN_PROGRESS}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(self.admin)
        response = self.client.patch(detail_url, {"status": Idea.Status.IN_PROGRESS}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Idea.Status.IN_PROGRESS)

    def test_vote_toggles_and_keeps_counter_in_sync(self):
        self.client.force_authenticate(self.admin)
        vote_url = reverse("idea-vote", args=[self.idea.id])

        response = self.client.post(vote_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_voted"])
        self.assertEqual(response.data["votes_count"], 1)

        response = self.client.post(vote_url)
        self.assertFalse(response.data["is_voted"])
        self.assertEqual(response.data["votes_count"], 0)
