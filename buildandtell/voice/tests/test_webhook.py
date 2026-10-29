import hashlib
import hmac
import json
import time

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from voice.models import VoiceCall, VoiceUsage
from voice.services.budget import current_period
from voice.services.webhook import verify_signature


TEST_SETTINGS = {
    'VOICE_CALLS_ENABLED': True,
    'ELEVENLABS_WEBHOOK_SECRET': 'test-secret',
    'VOICE_MONTHLY_MINUTES': 2,
    'VOICE_MAX_CALL_SECONDS': 120,
    'VOICE_DAILY_CALLS_PER_USER': 2,
    'VOICE_STALE_GRACE_SECONDS': 30,
}


def sign(body, secret='test-secret', timestamp=None):
    timestamp = str(int(timestamp if timestamp is not None else time.time()))
    digest = hmac.new(
        secret.encode('utf-8'),
        timestamp.encode('utf-8') + b'.' + body,
        hashlib.sha256,
    ).hexdigest()
    return f't={timestamp},v0={digest}'


@override_settings(**TEST_SETTINGS)
class WebhookTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.caller = User.objects.create_user('caller', password='pass')
        cls.callee = User.objects.create_user('callee', password='pass')

    def setUp(self):
        self.url = reverse('voice:elevenlabs_webhook')

    def make_call(self, conversation_id='conv-1', reserved_seconds=60):
        call = VoiceCall.objects.create(
            caller=self.caller,
            callee=self.callee,
            language='en',
            conversation_id=conversation_id,
            reserved_seconds=reserved_seconds,
        )
        VoiceUsage.objects.create(
            period=current_period(),
            reserved_seconds=reserved_seconds,
        )
        return call

    def post(self, payload, signature=None):
        body = json.dumps(payload).encode('utf-8')
        return self.client.post(
            self.url,
            data=body,
            content_type='application/json',
            HTTP_ELEVENLABS_SIGNATURE=signature or sign(body),
        )

    def test_settles_call_and_is_idempotent(self):
        call = self.make_call()
        payload = {
            'type': 'post_call_transcription',
            'data': {
                'conversation_id': 'conv-1',
                'metadata': {'call_duration_secs': 30},
            },
        }

        response = self.post(payload)
        self.assertEqual(response.status_code, 200)

        call.refresh_from_db()
        usage = VoiceUsage.objects.get(period=current_period())
        self.assertEqual(call.status, VoiceCall.Status.COMPLETED)
        self.assertEqual(call.billed_seconds, 30)
        self.assertEqual(call.settled_at is not None, True)
        self.assertEqual(usage.reserved_seconds, 0)
        self.assertEqual(usage.used_seconds, 30)

        response = self.post(payload)
        self.assertEqual(response.status_code, 200)
        usage.refresh_from_db()
        self.assertEqual(usage.used_seconds, 30)

    def test_initiation_failure_releases_call(self):
        call = self.make_call()

        response = self.post({
            'type': 'call_initiation_failure',
            'data': {'conversation_id': 'conv-1'},
        })

        self.assertEqual(response.status_code, 200)
        call.refresh_from_db()
        usage = VoiceUsage.objects.get(period=current_period())
        self.assertEqual(call.status, VoiceCall.Status.FAILED)
        self.assertEqual(call.billed_seconds, 0)
        self.assertEqual(usage.reserved_seconds, 0)
        self.assertEqual(usage.used_seconds, 0)

    def test_missing_duration_charges_reservation(self):
        call = self.make_call()

        self.post({
            'type': 'post_call_transcription',
            'data': {'conversation_id': 'conv-1'},
        })

        call.refresh_from_db()
        self.assertEqual(call.billed_seconds, call.reserved_seconds)

    def test_invalid_signature_is_rejected(self):
        call = self.make_call()
        body = json.dumps({
            'type': 'post_call_transcription',
            'data': {'conversation_id': 'conv-1'},
        }).encode('utf-8')

        response = self.client.post(
            self.url,
            data=body,
            content_type='application/json',
            HTTP_ELEVENLABS_SIGNATURE='t=1,v0=bad',
        )

        self.assertEqual(response.status_code, 401)
        call.refresh_from_db()
        self.assertEqual(call.status, VoiceCall.Status.RESERVED)

    @override_settings(ELEVENLABS_WEBHOOK_SECRET='')
    def test_missing_secret_is_unavailable(self):
        response = self.post({'type': 'post_call_transcription', 'data': {}})
        self.assertEqual(response.status_code, 503)

    def test_unknown_conversation_is_ignored(self):
        response = self.post({
            'type': 'post_call_transcription',
            'data': {'conversation_id': 'unknown'},
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ignored'])
        self.assertFalse(VoiceCall.objects.exists())


class SignatureTests(TestCase):
    def test_valid_and_tampered_signatures(self):
        body = b'{"hello":"world"}'
        header = sign(body)

        self.assertTrue(verify_signature(body, header, 'test-secret'))
        self.assertFalse(verify_signature(body + b'!', header, 'test-secret'))
        self.assertFalse(verify_signature(body, header, 'wrong-secret'))

    def test_expired_signature_is_rejected(self):
        body = b'{"hello":"world"}'
        header = sign(body, timestamp=time.time() - 1000)

        self.assertFalse(verify_signature(body, header, 'test-secret'))
