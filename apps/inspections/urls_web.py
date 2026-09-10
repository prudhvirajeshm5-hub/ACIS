from django.urls import path

from . import views

app_name = "inspections"

urlpatterns = [
    path("<uuid:pk>/", views.workspace, name="workspace"),
    path("<uuid:pk>/checklist/save/", views.save_checklist, name="save_checklist"),
    path("<uuid:pk>/glass/save/", views.save_glass, name="save_glass"),
    path("<uuid:pk>/accessories/save/", views.save_accessories, name="save_accessories"),
    path("<uuid:pk>/photos/upload/", views.upload_photo, name="upload_photo"),
    path("<uuid:pk>/videos/upload/", views.upload_video, name="upload_video"),
    path("<uuid:pk>/documents/<str:document_type>/toggle/", views.toggle_document, name="toggle_document"),
    path("<uuid:pk>/submit/", views.submit, name="submit"),
    path("<uuid:pk>/report/generate/", views.generate_report_view, name="generate_report"),
    path("reports/<uuid:report_pk>/", views.download_report, name="download_report"),
    path("<uuid:pk>/videos/<uuid:video_id>/view/", views.view_video, name="view_video"),
]
