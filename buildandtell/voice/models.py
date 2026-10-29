from django.conf import settings
from django.db import models


class VoiceProfile(models.Model):
    class Language(models.TextChoices):
        EN = 'en', 'English'
        ES = 'es', 'Spanish'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='voice_profile',
        on_delete=models.CASCADE,
    )
    enabled = models.BooleanField(default=False)
    default_language = models.CharField(
        max_length=2,
        choices=Language.choices,
        default=Language.EN,
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Voice profile of {self.user.username}'


class VoiceAgent(models.Model):
    profile = models.ForeignKey(
        VoiceProfile,
        related_name='agents',
        on_delete=models.CASCADE,
    )
    language = models.CharField(
        max_length=2,
        choices=VoiceProfile.Language.choices,
    )
    agent_id = models.CharField(max_length=64, blank=True)
    context_hash = models.CharField(max_length=64, blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    class Meta:
        ordering = ['language']
        constraints = [
            models.UniqueConstraint(
                fields=['profile', 'language'],
                name='uniq_voice_agent_profile_language',
            ),
        ]

    def __str__(self):
        return f'{self.profile.user.username} / {self.language}'


class VoiceCall(models.Model):
    class Status(models.TextChoices):
        RESERVED = 'reserved', 'Reserved'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        EXPIRED = 'expired', 'Expired'

    caller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='voice_calls_made',
        on_delete=models.CASCADE,
    )
    callee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='voice_calls_received',
        on_delete=models.CASCADE,
    )
    agent = models.ForeignKey(
        VoiceAgent,
        related_name='calls',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    language = models.CharField(
        max_length=2,
        choices=VoiceProfile.Language.choices,
    )
    conversation_id = models.CharField(max_length=128, blank=True, db_index=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.RESERVED,
    )
    reserved_seconds = models.PositiveIntegerField()
    billed_seconds = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    settled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['callee', 'status']),
            models.Index(fields=['caller', 'started_at']),
        ]

    def __str__(self):
        return f'{self.caller.username} -> {self.callee.username} ({self.status})'


class VoiceUsage(models.Model):
    period = models.CharField(max_length=7, unique=True)
    reserved_seconds = models.PositiveIntegerField(default=0)
    used_seconds = models.PositiveIntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-period']

    def __str__(self):
        return f'Voice usage {self.period}'
