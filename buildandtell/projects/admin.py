from django.contrib import admin
from .models import Project, BuildUpdate

# Register your models here.
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'slug', 'status', 'repo_url', 'website_url', 'created', 'updated']
    list_filter = ['created']
    search_fields = ['title', 'description']

@admin.register(BuildUpdate)
class BuildUpdateAdmin(admin.ModelAdmin):
    list_display = ['project', 'title', 'type', 'body', 'created', 'updated']
    list_filter = ['created']
    search_fields = ['title', 'body']