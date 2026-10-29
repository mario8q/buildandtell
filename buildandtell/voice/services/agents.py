from django.utils import timezone

from voice.models import VoiceAgent, VoiceProfile

from .context import build_agent_hash, build_context
from .elevenlabs import (
    ElevenLabsError,
    build_agent_payload,
    create_agent,
    delete_agent,
    update_agent,
)


def ensure_agent(profile, language):
    if language not in VoiceProfile.Language.values:
        raise ValueError(f'Unsupported language: {language}')

    user = profile.user
    context = build_context(user)
    context_hash = build_agent_hash(user, language, context)
    agent, _ = VoiceAgent.objects.get_or_create(
        profile=profile,
        language=language,
    )

    if agent.agent_id and agent.context_hash == context_hash:
        return agent

    payload = build_agent_payload(user, language, context)
    try:
        if agent.agent_id:
            update_agent(agent.agent_id, payload)
        else:
            agent.agent_id = create_agent(payload)
        agent.context_hash = context_hash
        agent.synced_at = timezone.now()
        agent.last_error = ''
        agent.save(
            update_fields=[
                'agent_id',
                'context_hash',
                'synced_at',
                'last_error',
            ]
        )
    except ElevenLabsError as exc:
        agent.last_error = str(exc)[:2000]
        agent.save(update_fields=['last_error'])
        raise
    return agent


def delete_profile_agents(profile):
    errors = []
    for agent in profile.agents.all():
        try:
            delete_agent(agent.agent_id)
        except ElevenLabsError as exc:
            agent.last_error = str(exc)[:2000]
            agent.save(update_fields=['last_error'])
            errors.append(f'{agent.language}: {exc}')
            continue
        agent.agent_id = ''
        agent.context_hash = ''
        agent.synced_at = None
        agent.last_error = ''
        agent.save(
            update_fields=[
                'agent_id',
                'context_hash',
                'synced_at',
                'last_error',
            ]
        )
    return errors
