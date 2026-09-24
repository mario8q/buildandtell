from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('user/<str:username>/', views.user_detail, name='user_detail')
]