from django.apps import AppConfig


class AnimeConfig(AppConfig):
    name = 'apps.anime'

    def ready(self):
        import apps.anime.application.read_model_signals
