import hashlib
import re

from django.conf import settings

from projects.models import BuildUpdate, Project

from .prompt import PROMPT_VERSION


CONTROL_CHARS = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')


def display_name(user):
    return user.get_full_name().strip() or user.username


def _clean(value, max_length=None):
    text = CONTROL_CHARS.sub('', value or '')
    text = text.replace('<', '‹').replace('>', '›')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip() + '…'
    return text


def _project_block(project, updates):
    technologies = ', '.join(
        _clean(technology.name, 40)
        for technology in project.technologies.all()
    )
    tags = ', '.join(
        _clean(tag.name, 40)
        for tag in project.tags.all()
    )
    lines = [
        f'- {_clean(project.title, 160)} '
        f'({project.get_status_display()}, updated {project.updated:%Y-%m-%d})',
    ]
    if technologies:
        lines.append(f'  Technologies: {technologies}')
    if tags:
        lines.append(f'  Tags: {tags}')
    if project.description:
        lines.append(f'  Description: {_clean(project.description, 700)}')
    if project.repo_url:
        lines.append(f'  Repository: {_clean(project.repo_url, 240)}')
    if project.website_url:
        lines.append(f'  Website: {_clean(project.website_url, 240)}')
    for update in updates:
        body = _clean(update.body, 320)
        lines.append(
            f'  Update {update.created:%Y-%m-%d} [{update.get_type_display()}]: '
            f'{_clean(update.title, 160)}'
            + (f' — {body}' if body else '')
        )
    return '\n'.join(lines)


def build_context(user):
    max_projects = settings.VOICE_CONTEXT_MAX_PROJECTS
    max_updates = settings.VOICE_CONTEXT_MAX_UPDATES

    projects = list(
        Project.objects.filter(user=user)
        .exclude(status=Project.Status.ARCHIVED)
        .prefetch_related('technologies', 'tags')
        .order_by('-updated')[:max_projects]
    )
    project_ids = [project.pk for project in projects]

    updates_by_project = {project_id: [] for project_id in project_ids}
    if project_ids:
        recent_updates = (
            BuildUpdate.objects.filter(project_id__in=project_ids)
            .select_related('project')
            .order_by('-created')[:max_updates]
        )
        for update in recent_updates:
            updates_by_project.setdefault(update.project_id, []).append(update)

    profile = getattr(user, 'profile', None)
    lines = [
        f'Builder: {display_name(user)} (@{user.username})',
    ]
    if profile and profile.bio:
        lines.append(f'Bio: {_clean(profile.bio, 1200)}')
    if profile and profile.website:
        lines.append(f'Website: {_clean(profile.website, 240)}')
    if profile and profile.github:
        lines.append(f'GitHub: {_clean(profile.github, 240)}')

    if projects:
        lines.append('')
        lines.append('Public projects (most recently updated first):')
        for project in projects:
            lines.append(_project_block(project, updates_by_project.get(project.pk, [])))
    else:
        lines.append('')
        lines.append('Public projects: none yet.')

    context = '\n'.join(lines).strip()
    max_chars = settings.VOICE_CONTEXT_MAX_CHARS
    if len(context) > max_chars:
        context = context[: max_chars - 20].rstrip() + '\n[context truncated]'
    return context


def build_agent_hash(user, language, context):
    voice_id = settings.ELEVENLABS_DEFAULT_VOICE_ID
    tts_model = (
        settings.ELEVENLABS_TTS_MODEL_ES
        if language == 'es'
        else settings.ELEVENLABS_TTS_MODEL_EN
    )
    parts = [
        PROMPT_VERSION,
        language,
        voice_id,
        tts_model,
        settings.ELEVENLABS_AGENT_LLM or '',
        str(settings.VOICE_MAX_CALL_SECONDS),
        context,
    ]
    return hashlib.sha256('\n'.join(parts).encode('utf-8')).hexdigest()
