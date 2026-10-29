from django.urls import path

from . import views

app_name = 'voice'

urlpatterns = [
    path('settings/', views.voice_settings, name='settings'),
    path(
        'settings/delete-agents/',
        views.delete_agents_view,
        name='delete_agents',
    ),
    path(
        'webhooks/elevenlabs/',
        views.elevenlabs_webhook,
        name='elevenlabs_webhook',
    ),
    path('<str:username>/token/', views.call_token, name='call_token'),
]
