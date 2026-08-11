from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from accounts.views import role_redirect_view, custom_login_view, register_view, home_view

urlpatterns = [
    path('admin/', admin.site.urls),

    # Home page
    path('', home_view, name='home'),

    # Auth
    path('login/', custom_login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', role_redirect_view, name='logout_redirect'),

    # Apps
    path('accounts/', include('accounts.urls')),
    path('conferences/', include('conferences.urls')),
    path('departments/', include('conferences.urls_departments')),
    path('submissions/', include('submissions.urls')),
    path('registrations/', include('registrations.urls')),
    path('payments/', include('payments.urls')),
    path('reports/', include('reports.urls')),
    path('dashboard/', include('accounts.urls_dashboard')),

    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
]

handler404 = 'conference_management.views.handler404'
handler500 = 'conference_management.views.handler500'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
