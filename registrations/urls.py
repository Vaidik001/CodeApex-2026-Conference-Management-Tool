from django.urls import path

from . import views

urlpatterns = [
    path('', views.my_registrations, name='my_registrations'),
    path('create/', views.registration_create, name='registration_create'),
    path('all/', views.all_registrations, name='all_registrations'),
]
