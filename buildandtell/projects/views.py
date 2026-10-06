from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.contrib.postgres.aggregates import StringAgg
from django.http import Http404
from taggit.models import Tag
from .models import Project, BuildUpdate
from .forms import CreateBuildUpdateForm, CreateProjectForm, SearchProjectForm


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

def project_list(request, tag_slug = None):
    tag = None
    if request.user.is_authenticated:
        list_projects = Project.objects.exclude(user=request.user, status=Project.Status.ARCHIVED)
    else:
        list_projects = Project.objects.all()
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        list_projects = list_projects.filter(tags__in=[tag])
    all_tags = Project.tags.most_common()
    paginator = Paginator(list_projects, 6)
    page_number = request.GET.get('page', 1)
    try:
        projects = paginator.page(page_number)
    except PageNotAnInteger:
        projects = paginator.page(1)
    except EmptyPage:
        projects = paginator.page(paginator.num_pages)
    return render(
        request,
        'project/list.html',
        {'projects': projects, 'tag': tag, 'all_tags': all_tags}
    )

@login_required
def project_user_list(request, username, tag_slug = None):
    tag = None
    list_projects = Project.objects.filter(user=request.user)
    all_user_tags = Project.tags.most_common(extra_filters={"project__user": request.user})
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        list_projects = list_projects.filter(tags__in=[tag])
    
    paginator = Paginator(list_projects, 3)
    page_number = request.GET.get('page', 1)
    try:
        projects = paginator.page(page_number)
    except PageNotAnInteger:
        projects = paginator.page(1)
    except EmptyPage:
        projects = paginator.page(paginator.num_pages)

    status_totals = {
        s['status']: s['total'] for s in list_projects.values('status').annotate(total=Count('id'))
    }
    update_count = BuildUpdate.objects.filter(project__user=request.user).count()
    return render(
        request,
        'project/user_list.html',
        {
            'projects': projects,
            'username': username,
            'tag': tag,
            'all_user_tags': all_user_tags,
            'status_totals': status_totals,
            'update_count': update_count,
        }
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
            project_form.save_m2m()
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

def project_search(request, filtrate):
    query = request.GET.get('query', '').strip()
    form = SearchProjectForm(request.GET or None)
    tag = None

    if filtrate == 'user':
        if not request.user.is_authenticated:
            return redirect('login')
        base = Project.objects.filter(user=request.user)
    elif filtrate == 'all':
        base = Project.objects.all()
    else:
        raise Http404("Invalid project filter")

    if request.user.is_authenticated:
        base = base.exclude(user=request.user, status=Project.Status.ARCHIVED)

    list_projects = base
    if query and form.is_valid():
        query = form.cleaned_data['query']
        tags_text = StringAgg('tagged_items__tag__name', delimiter=' ', distinct=True)
        vector = SearchVector('title', 'description', 'slug', weight='A') + SearchVector('tags_text', weight='B')
        list_projects = (
            base
            .annotate(tags_text=tags_text)
            .annotate(rank=SearchRank(vector, SearchQuery(query)))
            .filter(rank__gte=0.2)
            .order_by('-rank')
        )

    paginator = Paginator(list_projects, 6)
    page_num = request.GET.get('page', 1)
    try:
        projects = paginator.page(page_num)
    except PageNotAnInteger:
        projects = paginator.page(1)
    except EmptyPage:
        projects = paginator.page(paginator.num_pages)

    if filtrate == 'user':
        return render(
            request,
            'project/user_list.html',
            {
                'projects': projects,
                'username': request.user.username,
                'tag': tag,
                'all_user_tags': Project.tags.most_common(extra_filters={"project__user": request.user}),
                'status_totals': {
                    s['status']: s['total']
                    for s in base.values('status').annotate(total=Count('id'))
                },
                'update_count': BuildUpdate.objects.filter(project__user=request.user).count(),
                'query': query,
                'search_active': bool(query),
            }
        )

    return render(
        request,
        'project/list.html',
        {
            'projects': projects,
            'tag': tag,
            'all_tags': Project.tags.most_common(),
            'query': query,
            'search_active': bool(query),
        }
    )