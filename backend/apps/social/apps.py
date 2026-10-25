from django.apps import AppConfig


class SocialConfig(AppConfig):
    name = 'apps.social'

    def ready(self):
        import apps.social.application.signals
        import apps.social.application.signals_chat
