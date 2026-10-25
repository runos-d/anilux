import json
from types import SimpleNamespace
from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.anime.infrastructure.clients.animego_streams import (
    AlternativePlayback,
    AlternativeStream,
    AnimeGoStreamResolver,
)
from apps.anime.presentation.views.alternative_stream_views import _rewrite_playlist


class AnimeGoStreamResolverTests(SimpleTestCase):
    def test_resolve_keeps_aniboom_and_excludes_kodik(self):
        player_html = """
            <div id="provider">
              <button data-ptranslation="1" data-provider-title="Kodik"
                data-player="//kodikplayer.com/serial/1/hash/720p"
                data-translation-title="Main"></button>
              <button data-ptranslation="2" data-provider-title="AniBoom"
                data-player="//aniboom.one/embed/reserve"
                data-translation-title="Reserve"></button>
            </div>
        """
        parameters = json.dumps({
            "hls": json.dumps({"src": "https://media.example/master.m3u8"}),
        })
        embed_html = (
            '<video id="video" data-parameters="'
            + parameters.replace('"', '&quot;')
            + '"></video>'
        )
        resolver = AnimeGoStreamResolver()
        with (
            patch.object(resolver, "find_anime_id", return_value="126"),
            patch.object(
                resolver,
                "_player_payload",
                return_value=(player_html, (1, 2, 3), 1),
            ),
            patch.object(
                resolver,
                "_get",
                return_value=SimpleNamespace(text=embed_html),
            ),
        ):
            playback = resolver.resolve(
                title="Example",
                slug="example",
                title_en="Example",
                season=1,
                episode=1,
            )

        self.assertEqual((1, 2, 3), playback.episodes)
        self.assertEqual(1, len(playback.translations))
        self.assertEqual("Reserve", playback.translations[0].label)
        self.assertEqual("https://media.example/master.m3u8", playback.translations[0].url)

    def test_playlist_rewrite_proxies_variants_segments_and_uri_attributes(self):
        playlist = """#EXTM3U
#EXT-X-MAP:URI="init.mp4"
#EXTINF:4,
segment-1.m4s
"""
        rewritten = _rewrite_playlist(
            playlist,
            "https://media.example/path/video.m3u8",
            "https://aniboom.one/",
        )

        self.assertNotIn("segment-1.m4s\n", rewritten.replace("https%3A", ""))
        self.assertIn("/api/anime/alternative-stream/content/?token=", rewritten)
        self.assertEqual(2, rewritten.count("token="))


class AlternativeStreamsApiTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.anime = SimpleNamespace(
            pk=991234,
            shikimori_id=991234,
            slug="example",
            title_ru="Пример",
            title_en="Example",
            year=2024,
            kind="tv",
            status="finished",
        )

    @patch("apps.anime.presentation.views.alternative_stream_views.Anime.objects.get")
    @patch("apps.anime.presentation.views.alternative_stream_views.AnimeGoStreamResolver.resolve")
    def test_returns_neutral_stream_payload(self, resolve, get_anime):
        get_anime.return_value = self.anime
        resolve.return_value = AlternativePlayback(
            id="reserve",
            label="Резервный",
            translations=(
                AlternativeStream(
                    id="voice-1",
                    label="Озвучка",
                    url="https://media.example/master.m3u8",
                    referer="https://aniboom.one/",
                ),
            ),
            episodes=(1, 2, 3),
            selected_episode=2,
        )

        response = self.client.get(
            reverse("anime-alternative-streams", args=[self.anime.pk]),
            {"episode": 2, "season": 1},
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual("reserve", response.data["streams"][0]["id"])
        self.assertEqual("auto", response.data["streams"][0]["sources"][0]["quality"])
        self.assertEqual("voice-1", response.data["streams"][0]["translation_id"])
        self.assertEqual("Озвучка", response.data["streams"][0]["translations"][0]["name"])
        self.assertEqual([1, 2, 3], response.data["streams"][0]["episode_groups"][0]["episodes"])
        self.assertNotIn("animego", str(response.data).casefold())
        self.assertNotIn("aniboom", str(response.data).casefold())
