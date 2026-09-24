from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count
from .forms import UserRegistrationForm, UserEditForm, ProfileEditForm
from .models import Profile
from projects.models import BuildUpdate

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data["password"])
            new_user.save()
            messages.success(request, 'profile created successfully')
            return redirect('login')
        else:
            messages.error(request, 'there was an error with the form')
    else:
        form = UserRegistrationForm()
    return render(
        request,
        'account/create.html',
        {'form': form}
    )

def user_detail(request, username):
    user = get_object_or_404(get_user_model(), username=username)
    profile = get_object_or_404(Profile, user=user)
    projects = user.projects.prefetch_related('updates') # type: ignore
    status_totals = {
        s['status']: s['total']
        for s in projects.values('status').annotate(total=Count('id'))
    }
    recent_updates = (
        BuildUpdate.objects.filter(project__user=user)
        .select_related('project')
        .order_by('-created')[:10]
    )
    update_count = BuildUpdate.objects.filter(project__user=user).count()
    return render(
        request,
        'account/detail.html',
        {
            'profile': profile,
            'user': user,
            'projects': projects,
            'status_totals': status_totals,
            'recent_updates': recent_updates,
            'update_count': update_count,
        }
    )

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user_form = UserEditForm(data=request.POST, instance=request.user)
        profile_form = ProfileEditForm(data=request.POST, files=request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'profile updated successfully')
        else:
            messages.error(request, 'there was an error with the form')
    else:
        user_form = UserEditForm()
        profile_form = ProfileEditForm()
    return render(
        request,
        'account/edit.html',
        {'user_form': user_form, 'profile_form': profile_form}
    )