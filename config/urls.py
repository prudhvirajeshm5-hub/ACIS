from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="dashboard:home", permanent=False)),

    # Server-rendered app (Django templates)
    path("", include("apps.accounts.urls_web", namespace="accounts")),
    path("dashboard/", include("apps.mis.urls_dashboard", namespace="dashboard")),
    path("clients/", include("apps.insurers.urls_web", namespace="insurers")),
    path("mis/", include("apps.mis.urls_web", namespace="mis")),
    path("inspections/", include("apps.inspections.urls_web", namespace="inspections")),
    path("qc/", include("apps.qc.urls_web", namespace="qc")),

    # REST API (versioned; Flutter and any other client consumes only this)
    path("api/v1/", include("apps.api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
