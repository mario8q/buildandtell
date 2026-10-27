from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http.response import JsonResponse
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.contrib.auth.models import User
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
    is_following = False
    if request.user.is_authenticated:
        current_profile = request.user.profile
        if current_profile.following.filter(pk=profile.pk).exists():
            is_following = True
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
            'is_following': is_following,
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
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
    return render(
        request,
        'account/edit.html',
        {'user_form': user_form, 'profile_form': profile_form}
    )

@login_required
@require_POST
def user_follow(request, username):
    user_to_follow = get_object_or_404(get_user_model(), username=username)
    user_to_follow_profile = user_to_follow.profile # type: ignore
    profile = request.user.profile
    if profile.following.filter(pk=user_to_follow_profile.pk).exists():
        profile.following.remove(user_to_follow_profile) # type: ignore
        user_to_follow_profile.followers -= int(1)
        user_to_follow_profile.save()
        return JsonResponse({'action': 'unfollow', 'followers': user_to_follow_profile.followers})
    else:
        profile.following.add(user_to_follow_profile) # type: ignore
        user_to_follow_profile.followers += int(1)
        user_to_follow_profile.save()
        return JsonResponse({'action': 'follow', 'followers': user_to_follow_profile.followers})