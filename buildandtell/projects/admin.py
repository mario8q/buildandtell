from django.contrib import admin
from .models import Technology, Project, BuildUpdate

@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'slug', 'status', 'repo_url', 'website_url', 'created', 'updated']
    list_filter = ['created']
    search_fields = ['title', 'description']

@admin.register(BuildUpdate)
class BuildUpdateAdmin(admin.ModelAdmin):
    list_display = ['id', 'project', 'title', 'type', 'body', 'created', 'updated']
    list_filter = ['created']
    search_fields = ['title', 'body']