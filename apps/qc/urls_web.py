from django.urls import path

from . import views

app_name = "qc"

urlpatterns = [
    path("<uuid:pk>/", views.qc_review, name="review"),
]
