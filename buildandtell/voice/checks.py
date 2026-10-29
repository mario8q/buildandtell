from django.conf import settings
from django.core.checks import Warning, register


@register()
def voice_settings_check(app_configs, **kwargs):
    messages = []
    if not settings.VOICE_CALLS_ENABLED:
        return messages

    if not settings.ELEVENLABS_API_KEY:
        messages.append(
            Warning(
                'VOICE_CALLS_ENABLED is on but ELEVENLABS_API_KEY is empty.',
                hint='Set ELEVENLABS_API_KEY or disable VOICE_CALLS_ENABLED.',
                id='voice.W001',
            )
        )
    if not settings.ELEVENLABS_DEFAULT_VOICE_ID:
        messages.append(
            Warning(
                'VOICE_CALLS_ENABLED is on but no default voice is configured.',
                hint='Set ELEVENLABS_DEFAULT_VOICE_ID.',
                id='voice.W002',
            )
        )
    if not settings.ELEVENLABS_WEBHOOK_SECRET:
        messages.append(
            Warning(
                'VOICE_CALLS_ENABLED is on but ELEVENLABS_WEBHOOK_SECRET is empty.',
                hint='Configure a post-call webhook and set its signing secret.',
                id='voice.W003',
            )
        )
    return messages
