from django.urls import path

from . import views

urlpatterns = [
    path('', views.conference_list, name='conference_list'),
    path('materials/', views.materials_list, name='materials_list'),
    path('create/', views.conference_create, name='conference_create'),
    path('<int:pk>/', views.conference_detail, name='conference_detail'),
    path('<int:pk>/edit/', views.conference_update, name='conference_update'),
    path('<int:pk>/delete/', views.conference_delete, name='conference_delete'),
    path('<int:pk>/materials/upload/', views.material_upload, name='material_upload'),
    path('materials/<int:pk>/download/', views.material_download, name='material_download'),
    path('materials/<int:pk>/delete/', views.material_delete, name='material_delete'),
]
