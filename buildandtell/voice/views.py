import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import VoiceSettingsForm
from .models import VoiceCall, VoiceProfile
from .services.agents import delete_profile_agents, ensure_agent
from .services.budget import (
    VoiceBudgetError,
    max_call_seconds,
    release_call,
    remaining_seconds,
    reserve_call,
    settle_call,
)
from .services.elevenlabs import ElevenLabsError, get_conversation_token
from .services.webhook import verify_signature

logger = logging.getLogger(__name__)


def _json_error(message, code, status):
    return JsonResponse({'error': message, 'code': code}, status=status)


@login_required
def voice_settings(request):
    profile, _ = VoiceProfile.objects.get_or_create(user=request.user)
    form = VoiceSettingsForm(request.POST or None, instance=profile)

    if request.method == 'POST' and form.is_valid():
        profile = form.save()
        if profile.enabled and settings.VOICE_CALLS_ENABLED:
            try:
                ensure_agent(profile, VoiceProfile.Language.EN)
                ensure_agent(profile, VoiceProfile.Language.ES)
            except ElevenLabsError as exc:
                logger.warning('Could not prepare voice agents: %s', exc)
                messages.error(
                    request,
                    'Settings saved, but the AI agents could not be prepared. '
                    'Check the API key and try again.',
                )
            else:
                messages.success(request, 'AI voice settings updated.')
        else:
            messages.success(request, 'AI voice settings updated.')
        return redirect('voice:settings')

    agents = {agent.language: agent for agent in profile.agents.all()}
    return render(
        request,
        'voice/settings.html',
        {
            'form': form,
            'profile': profile,
            'agents': agents,
            'voice_calls_enabled': settings.VOICE_CALLS_ENABLED,
            'remaining_seconds': remaining_seconds(),
            'max_call_seconds': max_call_seconds(),
        },
    )


@login_required
@require_POST
def delete_agents_view(request):
    profile, _ = VoiceProfile.objects.get_or_create(user=request.user)
    errors = delete_profile_agents(profile)
    if errors:
        messages.error(
            request,
            'Some AI agents could not be deleted. Check the settings and retry.',
        )
    else:
        messages.success(request, 'AI agents deleted.')
    return redirect('voice:settings')


@require_POST
def call_token(request, username):
    if not request.user.is_authenticated:
        return _json_error('Log in to call an AI representative.', 'login_required', 401)
    if not settings.VOICE_CALLS_ENABLED:
        return _json_error('AI calls are currently disabled.', 'voice_disabled', 503)

    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except (UnicodeDecodeError, ValueError):
        data = request.POST
    if not isinstance(data, dict):
        data = request.POST

    user_model = get_user_model()
    try:
        callee = user_model.objects.get(username=username)
    except user_model.DoesNotExist:
        return _json_error('Builder not found.', 'not_found', 404)

    if callee.pk == request.user.pk:
        return _json_error('You cannot call your own AI representative.', 'self_call', 403)

    voice_profile = getattr(callee, 'voice_profile', None)
    if voice_profile is None or not voice_profile.enabled:
        return _json_error('This builder has not enabled AI calls.', 'voice_disabled', 403)

    language = data.get('language') or voice_profile.default_language
    if language not in VoiceProfile.Language.values:
        return _json_error('Unsupported language.', 'invalid_language', 400)

    try:
        call = reserve_call(
            caller=request.user,
            callee=callee,
            language=language,
        )
    except VoiceBudgetError as exc:
        return _json_error(exc.message, exc.code, exc.status_code)

    try:
        agent = ensure_agent(voice_profile, language)
        token_data = get_conversation_token(agent.agent_id)
    except ElevenLabsError:
        logger.exception('ElevenLabs could not start a call for %s', callee.username)
        release_call(call)
        return _json_error(
            'The AI representative is temporarily unavailable.',
            'provider_error',
            502,
        )

    call.agent = agent
    call.conversation_id = token_data['conversation_id']
    call.save(update_fields=['agent', 'conversation_id'])

    response = JsonResponse(
        {
            'token': token_data['token'],
            'conversation_id': token_data['conversation_id'],
            'call_id': call.pk,
            'max_seconds': call.reserved_seconds,
            'language': language,
        }
    )
    response['Cache-Control'] = 'no-store'
    return response


@csrf_exempt
@require_POST
def elevenlabs_webhook(request):
    secret = settings.ELEVENLABS_WEBHOOK_SECRET
    if not secret:
        return _json_error(
            'Webhook signing secret is not configured.',
            'webhook_not_configured',
            503,
        )

    signature = request.headers.get('ElevenLabs-Signature') or request.META.get(
        'HTTP_ELEVENLABS_SIGNATURE',
        '',
    )
    if not verify_signature(request.body, signature, secret):
        return _json_error('Invalid webhook signature.', 'invalid_signature', 401)

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, ValueError):
        return _json_error('Invalid webhook payload.', 'invalid_payload', 400)

    if not isinstance(payload, dict):
        return _json_error('Invalid webhook payload.', 'invalid_payload', 400)

    event_type = payload.get('type')
    data = payload.get('data') or {}
    if not isinstance(data, dict):
        data = {}
    conversation_id = data.get('conversation_id') or payload.get('conversation_id')
    if not conversation_id:
        return JsonResponse({'ok': True, 'ignored': True})

    call = VoiceCall.objects.filter(conversation_id=conversation_id).first()
    if call is None:
        return JsonResponse({'ok': True, 'ignored': True})

    if event_type == 'post_call_transcription':
        metadata = data.get('metadata') or {}
        if not isinstance(metadata, dict):
            metadata = {}
        duration = metadata.get('call_duration_secs')
        if duration is None:
            duration = data.get('call_duration_secs')
        if duration is None:
            duration = call.reserved_seconds
        call = settle_call(call, duration)
        logger.info(
            'voice.webhook settled call=%s conversation=%s seconds=%s',
            call.pk,
            conversation_id,
            call.billed_seconds,
        )
    elif event_type == 'call_initiation_failure':
        call = release_call(call)
        logger.info(
            'voice.webhook initiation_failed call=%s conversation=%s',
            call.pk,
            conversation_id,
        )

    return JsonResponse({'ok': True})
