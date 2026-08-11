from django.urls import path

from . import views

urlpatterns = [
    path('', views.all_payments, name='all_payments'),
    path('create/<int:reg_id>/', views.payment_create, name='payment_create'),
    path('receipt/<int:reg_id>/', views.payment_receipt, name='payment_receipt'),
]
