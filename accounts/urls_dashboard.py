from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard_redirect, name='dashboard_redirect'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('coordinator/', views.coordinator_dashboard, name='coordinator_dashboard'),
    path('author/', views.author_dashboard, name='author_dashboard'),
]
