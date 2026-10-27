from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'bio', 'get_projects_stars', 'get_following', 'followers', 'website', 'github']
    raw_id_fields = ['user']

    def get_projects_stars(self, obj):
        return ', '.join([project.title for project in obj.projects_stars.all()])
    get_projects_stars.short_description = 'Projects starred' # type: ignore

    def get_following(self, obj):
        return ', '.join([profile.user.username for profile in obj.following.all()])
    get_following.short_description = 'Following to' # type: ignore