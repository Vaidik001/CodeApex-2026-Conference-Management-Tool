from django.urls import path

from . import views

urlpatterns = [
    path('', views.reports_home, name='reports_home'),
    path('export/conferences/', views.conference_report_csv, name='conference_report_csv'),
    path('export/submissions/', views.submission_report_csv, name='submission_report_csv'),
    path('export/registrations/', views.registration_report_csv, name='registration_report_csv'),
    path('export/payments/', views.payment_report_csv, name='payment_report_csv'),
    path('export/departments/', views.department_report_csv, name='department_report_csv'),
]
