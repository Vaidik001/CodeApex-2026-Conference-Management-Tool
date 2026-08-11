from django.urls import path

from . import views

urlpatterns = [
    path('', views.my_submissions, name='my_submissions'),
    path('all/', views.all_submissions, name='all_submissions'),
    path('create/', views.submission_create, name='submission_create'),
    path('<int:pk>/', views.submission_detail, name='submission_detail'),
    path('<int:pk>/edit/', views.submission_update, name='submission_update'),
    path('<int:pk>/status/', views.submission_change_status, name='submission_change_status'),
]
