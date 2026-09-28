from django.urls import path

from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.attendance_home, name="home"),
    path("start/", views.start_shift, name="start"),
    path("end/", views.end_shift, name="end"),
]
