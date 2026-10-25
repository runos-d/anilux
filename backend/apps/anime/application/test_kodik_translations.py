from unittest.mock import patch

from django.test import SimpleTestCase

from apps.anime.application.anime_service import anime_service


class KodikTranslationSeasonsTests(SimpleTestCase):
    @patch("apps.anime.application.anime_service.external_anime_api.search")
    def test_groups_seasons_per_translation_without_mixing_sources(self, search):
        search.return_value = {
            "results": [
                {
                    "translation": {"id": 641, "title": "STEPonee", "type": "voice"},
                    "quality": "720",
                    "episodes_count": 68,
                    "last_season": 2,
                    "link": "//kodikplayer.com/serial/1/hash/720p",
                    "seasons": {
                        "2": {
                            "episodes": {
                                str(number): f"//kodik.example/{number}/720p"
                                for number in range(1, 69)
                            }
                        }
                    },
                },
                {
                    "translation": {"id": 1060, "title": "MiraiDUB", "type": "voice"},
                    "quality": "720",
                    "episodes_count": 4,
                    "last_season": 2,
                    "link": "//kodikplayer.com/serial/2/hash/720p",
                    "seasons": {
                        "0": {
                            "title": "Спешлы",
                            "episodes": {str(number): "//kodik.example/special" for number in range(1, 5)},
                        }
                    },
                },
                {
                    "translation": {"id": 1060, "title": "MiraiDUB", "type": "voice"},
                    "quality": "1080",
                    "episodes_count": 64,
                    "last_season": 2,
                    "link": "//kodikplayer.com/serial/3/hash/1080p",
                    "seasons": {
                        "2": {
                            "episodes": {
                                str(number): f"//kodik.example/{number}/1080p"
                                for number in range(1, 65)
                            }
                        }
                    },
                },
            ]
        }

        translations = anime_service.get_translations("5114")
        search.assert_called_once()
        self.assertTrue(search.call_args.kwargs["with_seasons"])
        by_id = {translation["id"]: translation for translation in translations}
        steponee = by_id[641]
        miraidub = by_id[1060]

        self.assertEqual(2, steponee["last_season"])
        self.assertEqual([1, 68], [steponee["seasons"]["2"]["episodes"][0], steponee["seasons"]["2"]["episodes"][-1]])
        self.assertEqual("Спешлы", miraidub["seasons"]["0"]["title"])
        self.assertEqual([1, 2, 3, 4], miraidub["seasons"]["0"]["episodes"])
        self.assertEqual([1, 64], [miraidub["seasons"]["2"]["episodes"][0], miraidub["seasons"]["2"]["episodes"][-1]])
        self.assertEqual(64, miraidub["total_episodes"])

    @patch("apps.anime.application.anime_service.external_anime_api.search")
    def test_returns_empty_seasons_when_kodik_has_no_metadata(self, search):
        search.return_value = {
            "results": [
                {
                    "translation": {"id": 77, "title": "Unknown", "type": "voice"},
                    "episodes_count": 12,
                    "last_season": 1,
                }
            ]
        }

        translations = anime_service.get_translations("1")

        self.assertEqual(1, len(translations))
        self.assertEqual({}, translations[0]["seasons"])
        self.assertEqual(1, translations[0]["last_season"])
