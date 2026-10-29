from django.apps import AppConfig


class VoiceConfig(AppConfig):
    name = 'voice'

    def ready(self):
        from . import checks  # noqa: F401
