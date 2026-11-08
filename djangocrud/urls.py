from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('', include('tasks.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
]

if not getattr(settings, 'DEMO_MODE', False):
    urlpatterns.insert(0, path('admin/', admin.site.urls))

# Configuración para servir archivos de medios locales (solo si no se usa Supabase Storage)
if not getattr(settings, 'USE_SUPABASE_STORAGE', False):
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]

handler400 = 'tasks.errors.bad_request'
handler403 = 'tasks.errors.permission_denied'
handler404 = 'tasks.errors.page_not_found'
handler500 = 'tasks.errors.server_error'

