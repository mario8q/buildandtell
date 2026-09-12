from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('edit/', views.edit_profile, name='edit_profile'),
]