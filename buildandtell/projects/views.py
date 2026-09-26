from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Project, BuildUpdate
from .forms import CreateBuildUpdateForm, CreateProjectForm

def dashboard(request):
    projects = Project.objects.select_related('user')
    recent_projects = projects[:3]
    recent_updates = (
        BuildUpdate.objects
        .select_related('project', 'project__user')[:5]
    )
    return render(
        request,
        'dashboard/dashboard.html',
        {
            'total_projects': projects.count(),
            'total_updates': BuildUpdate.objects.count(),
            'builders': get_user_model().objects.count(),
            'recent_projects': recent_projects,
            'recent_updates': recent_updates,
        }
    )

def project_list(request):
    if request.user.is_authenticated:
        projects = Project.objects.exclude(user=request.user, status=Project.Status.ARCHIVED)
    else:
        projects = Project.objects.all()
    return render(
        request,
        'project/list.html',
        {'projects': projects}
    )

@login_required
def project_user_list(request, username):
    projects = Project.objects.filter(user=request.user)
    return render(
        request,
        'project/user_list.html',
        {'projects': projects, 'username': username}
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
def project_edit(request, slug):
    project = get_object_or_404(Project, slug=slug, user=request.user)
    if request.method == 'POST':
        project_form = CreateProjectForm(request.POST, request.FILES,instance=project)
        if project_form.is_valid():
            project_form.save()
            messages.success(request,'Project updated successfully')
            return redirect(project.get_absolute_url())
        else:
            messages.error(request, 'there was an error with the form')
    else:
        project_form = CreateProjectForm(instance=project)
    return render(
        request,
        'project/edit.html',
        {'form': project_form,'project': project}
    )

@login_required
def project_delete(request, slug):
    project = get_object_or_404(Project, slug=slug, user=request.user)
    project.delete()
    messages.success(request, 'project deleted successfully')
    return redirect('projects:project_list')

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

@login_required
def build_update_edit(request, slug, id):
    project = get_object_or_404(Project, slug=slug, user=request.user)
    build_update = get_object_or_404(BuildUpdate, project=project, id=id)
    if request.method == 'POST':
        build_update_form = CreateBuildUpdateForm(request.POST, instance=build_update)
        if build_update_form.is_valid():
            build_update_form.save()
            messages.success(request, 'build update updated succsessfully')
        else:
            messages.error(request, 'there was an error with the form')
    else:
        build_update_form = CreateBuildUpdateForm(instance=build_update)
    return render(
        request,
        'build_update/edit.html',
        {'form': build_update_form, 'project': project}
    )

@login_required
def build_update_delete(request, slug):
    project = get_object_or_404(Project, slug=slug, user=request.user)
    build_update = get_object_or_404(BuildUpdate, project=project)
    build_update.delete()
    messages.success(request, 'build update deleted succsessfully')
    return redirect(project.get_absolute_url())