from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('create/', views.register, name='register'),
    path('edit/', views.edit_profile, name='edit_profile'),
]