from django.urls import path

from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('password/', views.change_password_view, name='change_password'),
    path('notifications/', views.notifications_view, name='notifications'),
]
