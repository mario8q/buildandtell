from django.contrib import admin

from .models import VoiceAgent, VoiceCall, VoiceProfile, VoiceUsage


@admin.register(VoiceProfile)
class VoiceProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'enabled', 'default_language', 'updated']
    list_filter = ['enabled', 'default_language']
    search_fields = ['user__username', 'user__email']
    raw_id_fields = ['user']


@admin.register(VoiceAgent)
class VoiceAgentAdmin(admin.ModelAdmin):
    list_display = ['profile', 'language', 'agent_id', 'synced_at', 'last_error']
    list_filter = ['language']
    search_fields = ['profile__user__username', 'agent_id']
    readonly_fields = ['agent_id', 'context_hash', 'synced_at', 'last_error']


@admin.register(VoiceCall)
class VoiceCallAdmin(admin.ModelAdmin):
    list_display = [
        'caller',
        'callee',
        'language',
        'status',
        'reserved_seconds',
        'billed_seconds',
        'started_at',
        'settled_at',
    ]
    list_filter = ['status', 'language']
    search_fields = [
        'caller__username',
        'callee__username',
        'conversation_id',
    ]
    readonly_fields = ['conversation_id', 'started_at', 'settled_at']
    date_hierarchy = 'started_at'


@admin.register(VoiceUsage)
class VoiceUsageAdmin(admin.ModelAdmin):
    list_display = ['period', 'reserved_seconds', 'used_seconds', 'updated']
    actions = ['reset_usage']

    @admin.action(description='Reset selected usage periods')
    def reset_usage(self, request, queryset):
        queryset.update(reserved_seconds=0, used_seconds=0)
