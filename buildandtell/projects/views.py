from django.shortcuts import render
from .models import Project, Documentation

def project_list(request):
    projects = Project.objects.exclude(status=Project.Status.ARCHIVED)
    return render(
        request,
        'project/list.html',
        {'projects': projects}
    )

def project_create(request):
    pass