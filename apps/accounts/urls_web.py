from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("logout-all/", views.logout_all_sessions, name="logout_all"),
    path("password/change/", views.ChangePasswordView.as_view(), name="change_password"),
    path(
        "password/reset/",
        auth_views.PasswordResetView.as_view(template_name="accounts/password_reset.html"),
        name="password_reset",
    ),
    path(
        "password/reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "password/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(template_name="accounts/password_reset_confirm.html"),
        name="password_reset_confirm",
    ),
    path(
        "password/reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/create/", views.create_user, name="create_user"),
    path("users/<uuid:pk>/clients/", views.manage_user_clients, name="manage_user_clients"),
    path("users/<uuid:pk>/reset-password/", views.admin_reset_password, name="admin_reset_password"),
    path("users/<uuid:pk>/toggle-active/", views.toggle_user_active, name="toggle_user_active"),
]
