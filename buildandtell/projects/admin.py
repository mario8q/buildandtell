from django.contrib import admin
from .models import Project, Documentation

# Register your models here.
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'status', 'repo_url', 'website_url', 'created']
    list_filter = ['created']
    search_fields = ['title', 'description']

@admin.register(Documentation)
class DocumentationAdmin(admin.ModelAdmin):
    list_display = ['project', 'title', 'body', 'order', 'created']
    list_filter = ['created']
    search_fields = ['title', 'body']