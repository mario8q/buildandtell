from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'bio', 'get_projects_stars', 'website', 'github']
    raw_id_fields = ['user']

    def get_projects_stars(self, obj):
        return ', '.join([project.title for project in obj.projects_stars.all()])
    get_projects_stars.short_description = 'Projects starred' # type: ignore