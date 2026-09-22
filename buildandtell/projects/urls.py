from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('create/', views.project_create, name='project_create'),
    path('<slug:slug>/edit/', views.project_edit, name='project_edit'),
    path('<slug:slug>/delete/', views.project_delete, name='project_delete'),
    path('<slug:slug>/build-update/create/', views.build_update_create, name='build_update_create'),
    path('<slug:slug>/build-update/edit/', views.build_update_edit, name='build_update_edit'),
    path('<slug:slug>/build-update/delete/', views.build_update_delete, name='build_update_delete'),
    path('<slug:slug>/', views.project_detail, name='project_detail'),
]