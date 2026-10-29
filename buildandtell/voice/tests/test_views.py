import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from account.models import Profile
from voice.models import VoiceAgent, VoiceCall, VoiceProfile, VoiceUsage
from voice.services.budget import current_period
from voice.services.elevenlabs import ElevenLabsError


TEST_SETTINGS = {
    'VOICE_CALLS_ENABLED': True,
    'ELEVENLABS_API_KEY': 'test-key',
    'ELEVENLABS_WEBHOOK_SECRET': 'test-secret',
    'ELEVENLABS_DEFAULT_VOICE_ID': 'voice-test',
    'VOICE_MONTHLY_MINUTES': 2,
    'VOICE_MAX_CALL_SECONDS': 120,
    'VOICE_DAILY_CALLS_PER_USER': 2,
    'VOICE_STALE_GRACE_SECONDS': 30,
}


@override_settings(**TEST_SETTINGS)
class VoiceSettingsViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user('owner', password='pass')
        Profile.objects.get_or_create(user=cls.user)

    def setUp(self):
        self.client.force_login(self.user)

    def test_settings_page_creates_profile(self):
        response = self.client.get(reverse('voice:settings'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(VoiceProfile.objects.filter(user=self.user).exists())

    @patch('voice.views.ensure_agent')
    def test_enabling_prepares_both_agents(self, ensure_agent):
        response = self.client.post(
            reverse('voice:settings'),
            {'enabled': 'on', 'default_language': 'es'},
        )
        self.assertRedirects(response, reverse('voice:settings'))
        profile = VoiceProfile.objects.get(user=self.user)
        self.assertTrue(profile.enabled)
        self.assertEqual(profile.default_language, 'es')
        self.assertEqual(ensure_agent.call_count, 2)

    @patch('voice.views.delete_profile_agents', return_value=[])
    def test_delete_agents(self, delete_profile_agents):
        response = self.client.post(reverse('voice:delete_agents'))
        self.assertRedirects(response, reverse('voice:settings'))
        delete_profile_agents.assert_called_once()


@override_settings(**TEST_SETTINGS)
class CallTokenViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.caller = User.objects.create_user('caller', password='pass')
        cls.owner = User.objects.create_user('owner', password='pass')
        cls.other = User.objects.create_user('other', password='pass')
        Profile.objects.get_or_create(user=cls.caller)
        Profile.objects.get_or_create(user=cls.owner)
        Profile.objects.get_or_create(user=cls.other)
        cls.voice_profile = VoiceProfile.objects.create(
            user=cls.owner,
            enabled=True,
            default_language='en',
        )
        cls.agent = VoiceAgent.objects.create(
            profile=cls.voice_profile,
            language='en',
            agent_id='agent-en',
        )

    def setUp(self):
        self.client.force_login(self.caller)
        self.url = reverse('voice:call_token', args=[self.owner.username])

    def _post(self, payload=None):
        return self.client.post(
            self.url,
            data=json.dumps(payload or {}),
            content_type='application/json',
        )

    @patch('voice.views.get_conversation_token')
    @patch('voice.views.ensure_agent')
    def test_token_reserves_call(self, ensure_agent, get_conversation_token):
        ensure_agent.return_value = self.agent
        get_conversation_token.return_value = {
            'token': 'conv-token',
            'conversation_id': 'conv-1',
        }

        response = self._post({'language': 'en'})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['token'], 'conv-token')
        self.assertEqual(data['max_seconds'], 120)
        call = VoiceCall.objects.get()
        self.assertEqual(call.status, VoiceCall.Status.RESERVED)
        self.assertEqual(call.conversation_id, 'conv-1')
        self.assertEqual(call.agent, self.agent)
        usage = VoiceUsage.objects.get(period=current_period())
        self.assertEqual(usage.reserved_seconds, 120)

    @patch('voice.views.ensure_agent')
    def test_provider_failure_releases_reservation(self, ensure_agent):
        ensure_agent.side_effect = ElevenLabsError('provider down')

        response = self._post()

        self.assertEqual(response.status_code, 502)
        call = VoiceCall.objects.get()
        self.assertEqual(call.status, VoiceCall.Status.FAILED)
        usage = VoiceUsage.objects.get(period=current_period())
        self.assertEqual(usage.reserved_seconds, 0)

    def test_anonymous_is_rejected(self):
        self.client.logout()
        response = self._post()
        self.assertEqual(response.status_code, 401)

    @override_settings(VOICE_CALLS_ENABLED=False)
    def test_flag_off(self):
        response = self._post()
        self.assertEqual(response.status_code, 503)

    def test_self_call_is_rejected(self):
        self.client.force_login(self.owner)
        response = self._post()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['code'], 'self_call')

    def test_non_opted_in_builder_is_rejected(self):
        self.client.force_login(self.caller)
        response = self.client.post(
            reverse('voice:call_token', args=[self.other.username]),
            data='{}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    def test_invalid_language_is_rejected(self):
        response = self._post({'language': 'fr'})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(VoiceCall.objects.exists())

    def test_budget_exhausted(self):
        VoiceUsage.objects.create(
            period=current_period(),
            used_seconds=120,
        )
        response = self._post()
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()['code'], 'budget_exhausted')

    @override_settings(VOICE_DAILY_CALLS_PER_USER=1)
    def test_daily_limit(self):
        VoiceCall.objects.create(
            caller=self.caller,
            callee=self.owner,
            language='en',
            reserved_seconds=120,
            status=VoiceCall.Status.COMPLETED,
        )
        response = self._post()
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()['code'], 'daily_limit')

    def test_callee_busy(self):
        VoiceCall.objects.create(
            caller=self.other,
            callee=self.owner,
            language='en',
            reserved_seconds=120,
        )
        response = self._post()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['code'], 'callee_busy')


@override_settings(**TEST_SETTINGS)
class AccountVoiceIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.caller = User.objects.create_user('caller', password='pass')
        cls.owner = User.objects.create_user('owner', password='pass')
        cls.plain = User.objects.create_user('plain', password='pass')
        for user in (cls.caller, cls.owner, cls.plain):
            Profile.objects.get_or_create(user=user)
        VoiceProfile.objects.create(
            user=cls.owner,
            enabled=True,
            default_language='es',
        )

    def test_caller_sees_call_button_and_dialog(self):
        self.client.force_login(self.caller)
        response = self.client.get(
            reverse('account:user_detail', args=[self.owner.username])
        )
        self.assertContains(response, 'Call AI')
        self.assertContains(response, 'voice-call-dialog')
        self.assertContains(response, 'voice-call.js')

    def test_owner_sees_settings_link(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse('account:user_detail', args=[self.owner.username])
        )
        self.assertContains(response, 'AI voice settings')

    @override_settings(VOICE_CALLS_ENABLED=False)
    def test_call_button_hidden_when_disabled(self):
        self.client.force_login(self.caller)
        response = self.client.get(
            reverse('account:user_detail', args=[self.owner.username])
        )
        self.assertNotContains(response, 'Call AI')

    def test_edit_profile_links_to_voice_settings(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('account:edit_profile'))
        self.assertContains(response, 'AI voice settings')
