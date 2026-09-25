from django.urls import path

from . import views

app_name = "mis"

urlpatterns = [
    path("", views.MISListView.as_view(), name="list"),
    path("create/", views.CreateMISWizardView.as_view(), name="create"),
    path("create/<int:step>/", views.CreateMISWizardView.as_view(), name="create"),
    path("<uuid:pk>/", views.MISDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.MISEditView.as_view(), name="edit"),
]
