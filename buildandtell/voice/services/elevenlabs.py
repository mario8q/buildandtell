import requests
from django.conf import settings

from .prompt import build_prompt, first_message


class ElevenLabsError(Exception):
    def __init__(self, message, status_code=None, code=None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code


def _headers():
    if not settings.ELEVENLABS_API_KEY:
        raise ElevenLabsError(
            'ELEVENLABS_API_KEY is not configured.',
            code='missing_api_key',
        )
    return {
        'xi-api-key': settings.ELEVENLABS_API_KEY,
        'Content-Type': 'application/json',
    }


def _request(method, path, **kwargs):
    url = f'{settings.ELEVENLABS_API_BASE.rstrip("/")}/{path.lstrip("/")}'
    try:
        response = requests.request(
            method,
            url,
            headers=_headers(),
            timeout=20,
            **kwargs,
        )
    except requests.RequestException as exc:
        raise ElevenLabsError(
            f'ElevenLabs request failed: {exc}',
            code='request_failed',
        ) from exc

    if response.status_code >= 400:
        message = f'ElevenLabs returned {response.status_code}.'
        code = None
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict):
            detail = payload.get('detail')
            if isinstance(detail, dict):
                message = detail.get('message') or message
                code = detail.get('code')
            elif isinstance(detail, str):
                message = detail
        raise ElevenLabsError(message, status_code=response.status_code, code=code)

    return response


def tts_model_for(language):
    if language == 'es':
        return settings.ELEVENLABS_TTS_MODEL_ES
    return settings.ELEVENLABS_TTS_MODEL_EN


def build_agent_payload(user, language, context):
    prompt = build_prompt(user, language, context)
    payload = {
        'name': f'Build&Tell AI · @{user.username} · {language}',
        'tags': ['buildandtell', f'user:{user.pk}', f'lang:{language}'],
        'conversation_config': {
            'agent': {
                'first_message': first_message(user, language),
                'language': language,
                'prompt': {'prompt': prompt},
            },
            'tts': {
                'voice_id': settings.ELEVENLABS_DEFAULT_VOICE_ID,
                'model_id': tts_model_for(language),
            },
            'conversation': {
                'max_duration_seconds': settings.VOICE_MAX_CALL_SECONDS,
            },
        },
        'platform_settings': {
            'call_limits': {
                'agent_concurrency_limit': 1,
                'daily_limit': 10,
                'bursting_enabled': False,
            },
            'trust_context': 'low',
            'privacy': {
                'record_voice': False,
                'delete_transcript_and_pii': True,
            },
        },
    }
    if settings.ELEVENLABS_AGENT_LLM:
        payload['conversation_config']['agent']['prompt']['llm'] = (
            settings.ELEVENLABS_AGENT_LLM
        )
    return payload


def create_agent(payload):
    response = _request('POST', 'convai/agents/create', json=payload)
    data = response.json()
    agent_id = data.get('agent_id')
    if not agent_id:
        raise ElevenLabsError('ElevenLabs did not return an agent id.')
    return agent_id


def update_agent(agent_id, payload):
    _request('PATCH', f'convai/agents/{agent_id}', json=payload)


def delete_agent(agent_id):
    if not agent_id:
        return
    try:
        _request('DELETE', f'convai/agents/{agent_id}')
    except ElevenLabsError as exc:
        if exc.status_code == 404:
            return
        raise


def get_conversation_token(agent_id):
    response = _request(
        'GET',
        'convai/conversation/token',
        params={'agent_id': agent_id},
    )
    data = response.json()
    if not data.get('token') or not data.get('conversation_id'):
        raise ElevenLabsError('ElevenLabs did not return a conversation token.')
    return {
        'token': data['token'],
        'conversation_id': data['conversation_id'],
    }
