from django.urls import path

from . import views

app_name = "incentives"

urlpatterns = [
    path("", views.my_targets, name="my"),
    path("manage/", views.manage_targets, name="manage"),
    path("manage/<uuid:pk>/delete/", views.delete_target, name="delete"),
]
