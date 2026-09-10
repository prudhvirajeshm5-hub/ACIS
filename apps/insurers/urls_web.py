from django.urls import path

from . import views

app_name = "insurers"

urlpatterns = [
    path("", views.ClientListView.as_view(), name="list"),
    path("create/", views.ClientCreateView.as_view(), name="create"),
    path("branches/create/", views.BranchCreateView.as_view(), name="create_branch"),
]
