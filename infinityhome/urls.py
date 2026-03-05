from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('demandes/', include('apps.demandes.urls')),
    path('techniciens/', include('apps.techniciens.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    # DRF API
    path('api/v1/', include('apps.api.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
