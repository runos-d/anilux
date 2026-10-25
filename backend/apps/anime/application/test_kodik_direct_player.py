from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.anime.infrastructure.models.anime import Anime


class KodikDirectPlayerTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.anime = Anime.objects.create(
            title_ru="Прямой поток",
            title_en="Direct stream",
            slug="direct-stream",
            shikimori_id=12345,
            kodik_link="//kodikplayer.com/serial/1/hash/720p",
        )

    @patch("apps.anime.presentation.views.anime_views.anime_service.get_video_links")
    @patch("apps.anime.presentation.views.anime_views.anime_service.get_episode_info")
    def test_returns_quality_sources_for_direct_cdn_delivery(self, get_episode_info, get_video_links):
        get_episode_info.return_value = {
            "url": "//kodikplayer.com/seria/2/hash/720p",
            "screenshots": ["https://i.kodikres.com/screenshots/seria/2/1.jpg"],
        }
        get_video_links.return_value = {
            "360": "https://cdn.example/360.m3u8",
            "1080": "https://cdn.example/1080.m3u8",
            "720": "https://cdn.example/720.m3u8",
        }

        response = self.client.get(
            f"/api/anime/{self.anime.pk}/kodik_video_url/",
            {"episode": 2, "season": 1, "translation_id": 77},
            HTTP_X_FORWARDED_FOR="203.0.113.7, 10.0.0.2",
        )

        self.assertEqual(200, response.status_code, response.data)
        self.assertEqual("direct", response.data["delivery"])
        self.assertEqual(["1080", "720", "360"], [item["quality"] for item in response.data["sources"]])
        self.assertEqual(
            "https://i.kodikres.com/screenshots/seria/2/1.jpg",
            response.data["preview"],
        )
        self.assertEqual("private, no-store", response["Cache-Control"])
        get_episode_info.assert_called_once_with("12345", 2, "1", "77")
        get_video_links.assert_called_once_with("//kodikplayer.com/seria/2/hash/720p", "203.0.113.7")

    @patch("apps.anime.presentation.views.anime_views.anime_service.get_video_links")
    @patch("apps.anime.presentation.views.anime_views.anime_service.get_episode_info")
    def test_reports_kodik_fallback_when_direct_api_is_unavailable(self, get_episode_info, get_video_links):
        get_episode_info.return_value = {
            "url": "//kodikplayer.com/seria/2/hash/720p",
            "screenshots": [],
        }
        get_video_links.side_effect = RuntimeError("Kodik video API credentials are not configured")

        response = self.client.get(f"/api/anime/{self.anime.pk}/kodik_video_url/")

        self.assertEqual(503, response.status_code)
        self.assertEqual("kodik", response.data["fallback"])
