from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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

@login_required
def project_create(request):
    if request.method == 'POST':
        project_form = CreateProjectForm(request.POST, request.FILES)
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

@login_required
def build_update_create(request, slug):
    project = get_object_or_404(Project, slug=slug, user=request.user)
    if request.method == 'POST':
        build_update_form = CreateBuildUpdateForm(request.POST)
        if build_update_form.is_valid():
            new_build_update = build_update_form.save(commit=False)
            new_build_update.project = project
            new_build_update.save()
            messages.success(request, 'build update created succsessfully')
            return redirect(project.get_absolute_url())
        else:
            messages.error(request, 'there was an error with the form')
    else:
        build_update_form = CreateBuildUpdateForm()
    return render (
        request,
        'build_update/create.html',
        {'form': build_update_form, 'project': project}
    )