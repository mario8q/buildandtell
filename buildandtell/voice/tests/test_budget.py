from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from voice.models import VoiceCall, VoiceUsage
from voice.services.budget import (
    BudgetExceeded,
    CalleeBusy,
    DailyLimitExceeded,
    current_period,
    expire_stale_calls,
    release_call,
    reserve_call,
    settle_call,
)


TEST_SETTINGS = {
    'VOICE_CALLS_ENABLED': True,
    'VOICE_MONTHLY_MINUTES': 2,
    'VOICE_MAX_CALL_SECONDS': 60,
    'VOICE_DAILY_CALLS_PER_USER': 2,
    'VOICE_STALE_GRACE_SECONDS': 30,
}


@override_settings(**TEST_SETTINGS)
class BudgetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.caller = User.objects.create_user('caller', password='pass')
        cls.other_caller = User.objects.create_user('other', password='pass')
        cls.callee = User.objects.create_user('callee', password='pass')

    def test_reserve_and_settle(self):
        call = reserve_call(self.caller, self.callee, 'en')
        usage = VoiceUsage.objects.get(period=current_period())

        self.assertEqual(call.status, VoiceCall.Status.RESERVED)
        self.assertEqual(call.reserved_seconds, 60)
        self.assertEqual(usage.reserved_seconds, 60)

        call = settle_call(call, 25)
        usage.refresh_from_db()

        self.assertEqual(call.status, VoiceCall.Status.COMPLETED)
        self.assertEqual(call.billed_seconds, 25)
        self.assertEqual(usage.reserved_seconds, 0)
        self.assertEqual(usage.used_seconds, 25)

    def test_release_refunds_reservation(self):
        call = reserve_call(self.caller, self.callee, 'en')
        call = release_call(call)
        usage = VoiceUsage.objects.get(period=current_period())

        self.assertEqual(call.status, VoiceCall.Status.FAILED)
        self.assertEqual(call.billed_seconds, 0)
        self.assertEqual(usage.reserved_seconds, 0)
        self.assertEqual(usage.used_seconds, 0)

    def test_budget_exhausted(self):
        VoiceUsage.objects.create(
            period=current_period(),
            used_seconds=120,
        )
        with self.assertRaises(BudgetExceeded):
            reserve_call(self.caller, self.callee, 'en')

    @override_settings(VOICE_DAILY_CALLS_PER_USER=1)
    def test_daily_limit(self):
        VoiceCall.objects.create(
            caller=self.caller,
            callee=self.callee,
            language='en',
            reserved_seconds=60,
            status=VoiceCall.Status.COMPLETED,
        )
        with self.assertRaises(DailyLimitExceeded):
            reserve_call(self.caller, self.callee, 'en')

    def test_callee_busy(self):
        reserve_call(self.caller, self.callee, 'en')
        with self.assertRaises(CalleeBusy):
            reserve_call(self.other_caller, self.callee, 'en')

    def test_stale_call_is_expired_and_charged(self):
        call = reserve_call(self.caller, self.callee, 'en')
        VoiceCall.objects.filter(pk=call.pk).update(
            started_at=timezone.now() - timedelta(seconds=200)
        )

        expire_stale_calls()

        call.refresh_from_db()
        usage = VoiceUsage.objects.get(period=current_period())
        self.assertEqual(call.status, VoiceCall.Status.EXPIRED)
        self.assertEqual(call.billed_seconds, call.reserved_seconds)
        self.assertEqual(usage.reserved_seconds, 0)
        self.assertEqual(usage.used_seconds, call.reserved_seconds)
