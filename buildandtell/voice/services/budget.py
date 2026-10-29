from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from voice.models import VoiceCall, VoiceUsage


class VoiceBudgetError(Exception):
    code = 'voice_unavailable'
    status_code = 429

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class BudgetExceeded(VoiceBudgetError):
    code = 'budget_exhausted'
    status_code = 429


class DailyLimitExceeded(VoiceBudgetError):
    code = 'daily_limit'
    status_code = 429


class CalleeBusy(VoiceBudgetError):
    code = 'callee_busy'
    status_code = 409


def monthly_limit_seconds():
    return max(0, settings.VOICE_MONTHLY_MINUTES * 60)


def max_call_seconds():
    return min(
        max(1, settings.VOICE_MAX_CALL_SECONDS),
        monthly_limit_seconds(),
    )


def current_period(now=None):
    now = now or timezone.now()
    return now.strftime('%Y-%m')


def _period_for(dt):
    return dt.strftime('%Y-%m')


def _usage_for_update(period):
    try:
        with transaction.atomic():
            usage, _ = VoiceUsage.objects.get_or_create(period=period)
    except IntegrityError:
        usage = VoiceUsage.objects.get(period=period)
    return VoiceUsage.objects.select_for_update().get(pk=usage.pk)


def remaining_seconds(period=None):
    period = period or current_period()
    usage = VoiceUsage.objects.filter(period=period).first()
    used = usage.used_seconds if usage else 0
    reserved = usage.reserved_seconds if usage else 0
    return max(0, monthly_limit_seconds() - used - reserved)


def expire_stale_calls(now=None):
    now = now or timezone.now()
    cutoff = now - timedelta(
        seconds=max_call_seconds() + settings.VOICE_STALE_GRACE_SECONDS
    )
    stale_ids = list(
        VoiceCall.objects.filter(
            status=VoiceCall.Status.RESERVED,
            started_at__lt=cutoff,
        ).values_list('pk', flat=True)[:100]
    )
    for call_id in stale_ids:
        with transaction.atomic():
            call = VoiceCall.objects.select_for_update().get(pk=call_id)
            if call.status != VoiceCall.Status.RESERVED:
                continue
            usage = _usage_for_update(_period_for(call.started_at))
            usage.reserved_seconds = max(
                0,
                usage.reserved_seconds - call.reserved_seconds,
            )
            usage.used_seconds += call.reserved_seconds
            usage.save(update_fields=['reserved_seconds', 'used_seconds', 'updated'])
            call.status = VoiceCall.Status.EXPIRED
            call.billed_seconds = call.reserved_seconds
            call.settled_at = now
            call.save(
                update_fields=[
                    'status',
                    'billed_seconds',
                    'settled_at',
                ]
            )


def reserve_call(caller, callee, language, agent=None):
    expire_stale_calls()
    now = timezone.now()
    reserved_seconds = max_call_seconds()

    with transaction.atomic():
        usage = _usage_for_update(current_period(now))
        available = (
            monthly_limit_seconds()
            - usage.used_seconds
            - usage.reserved_seconds
        )
        if reserved_seconds <= 0 or available < reserved_seconds:
            raise BudgetExceeded(
                'The shared AI call minutes for this month are used up.'
            )

        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        calls_today = VoiceCall.objects.filter(
            caller=caller,
            started_at__gte=day_start,
        ).count()
        if calls_today >= settings.VOICE_DAILY_CALLS_PER_USER:
            raise DailyLimitExceeded(
                'You have reached your AI call limit for today.'
            )

        active_since = now - timedelta(
            seconds=reserved_seconds + settings.VOICE_STALE_GRACE_SECONDS
        )
        if VoiceCall.objects.filter(
            callee=callee,
            status=VoiceCall.Status.RESERVED,
            started_at__gte=active_since,
        ).exists():
            raise CalleeBusy(
                'This AI representative is already on another call.'
            )

        call = VoiceCall.objects.create(
            caller=caller,
            callee=callee,
            agent=agent,
            language=language,
            reserved_seconds=reserved_seconds,
        )
        usage.reserved_seconds = F('reserved_seconds') + reserved_seconds
        usage.save(update_fields=['reserved_seconds', 'updated'])
    call.refresh_from_db()
    return call


def settle_call(call, billed_seconds):
    now = timezone.now()
    with transaction.atomic():
        call = VoiceCall.objects.select_for_update().get(pk=call.pk)
        if call.status != VoiceCall.Status.RESERVED:
            return call
        actual = max(0, int(billed_seconds or 0))
        actual = min(actual, call.reserved_seconds)
        usage = _usage_for_update(_period_for(call.started_at))
        usage.reserved_seconds = max(
            0,
            usage.reserved_seconds - call.reserved_seconds,
        )
        usage.used_seconds = F('used_seconds') + actual
        usage.save(update_fields=['reserved_seconds', 'used_seconds', 'updated'])
        call.billed_seconds = actual
        call.status = VoiceCall.Status.COMPLETED
        call.settled_at = now
        call.save(
            update_fields=[
                'billed_seconds',
                'status',
                'settled_at',
            ]
        )
    call.refresh_from_db()
    return call


def release_call(call, status=VoiceCall.Status.FAILED):
    now = timezone.now()
    with transaction.atomic():
        call = VoiceCall.objects.select_for_update().get(pk=call.pk)
        if call.status != VoiceCall.Status.RESERVED:
            return call
        usage = _usage_for_update(_period_for(call.started_at))
        usage.reserved_seconds = max(
            0,
            usage.reserved_seconds - call.reserved_seconds,
        )
        usage.save(update_fields=['reserved_seconds', 'updated'])
        call.billed_seconds = 0
        call.status = status
        call.settled_at = now
        call.save(
            update_fields=[
                'billed_seconds',
                'status',
                'settled_at',
            ]
        )
    call.refresh_from_db()
    return call
