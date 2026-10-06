from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # List projects
    path('', views.project_list, name='project_list'),
    path('<slug:tag_slug>/tag/', views.project_list, name='project_list_by_tag'),
    # Search projects
    path('user/search/', views.project_search, {'filtrate': 'user'}, name='project_user_search'),
    path('all/search/', views.project_search, {'filtrate': 'all'}, name='project_search'),
    path('user/<str:username>/tag/<slug:tag_slug>/', views.project_user_list, name='project_user_list_by_tag'),
    path('user/<str:username>/', views.project_user_list, name='project_user_list'),
    # Crud projects
    path('create/', views.project_create, name='project_create'),
    path('<slug:slug>/edit/', views.project_edit, name='project_edit'),
    path('<slug:slug>/delete/', views.project_delete, name='project_delete'),
    # Crud build update
    path('<slug:slug>/build-update/create/', views.build_update_create, name='build_update_create'),
    path('<slug:slug>/build-update/<int:id>/edit/', views.build_update_edit, name='build_update_edit'),
    path('<slug:slug>/build-update/delete/', views.build_update_delete, name='build_update_delete'),
    path('<slug:slug>/', views.project_detail, name='project_detail'),
]