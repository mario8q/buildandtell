from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Project, BuildUpdate
from .forms import CreateBuildUpdateForm, CreateProjectForm

def project_list(request):
    projects = Project.objects.exclude(status=Project.Status.ARCHIVED)
    return render(
        request,
        'project/list.html',
        {'projects': projects}
    )

def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug)
    return render(
        request,
        'project/detail.html',
        {'project': project}
    )

def project_create(request):
    if request.method == 'POST':
        project_form = CreateProjectForm(request.POST)
        if project_form.is_valid():
            new_project = project_form.save(commit=False)
            new_project.user = request.user
            new_project.save()
            messages.success(request, 'project created succsessfully')
            return redirect(new_project.get_absolute_url())
        else:
            messages.error(request, 'there was an error with the form')
    else:
        project_form = CreateProjectForm()
        return render(
            request,
            'project/create.html',
            {'form': project_form}
        )

def build_update_create(request):
    pass