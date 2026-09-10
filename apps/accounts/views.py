import secrets

from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView

from .forms import ForcedPasswordChangeForm, LoginForm, UserClientsForm, UserCreateForm
from .models import LoginHistory
from .permissions import PermissionRequiredMixin

User = get_user_model()

FAILED_LOGIN_LIMIT = 5


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")


class LoginView(DjangoLoginView):
    template_name = "accounts/login.html"
    form_class = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()

        if user.is_locked:
            messages.error(self.request, "This account is locked after too many failed attempts. Contact your administrator.")
            return self.form_invalid(form)

        response = super().form_valid(form)

        if not form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(0)

        LoginHistory.objects.create(
            user=user, ip_address=_client_ip(self.request),
            user_agent=self.request.META.get("HTTP_USER_AGENT", "")[:255], successful=True,
        )

        if user.must_change_password:
            messages.info(self.request, "Please set a new password before continuing.")
            return redirect("accounts:change_password")

        return response

    def form_invalid(self, form):
        username = form.data.get("username")
        if username:
            user = User.objects.filter(username__iexact=username).first() or User.objects.filter(email__iexact=username).first()
            if user:
                LoginHistory.objects.create(
                    user=user, ip_address=_client_ip(self.request),
                    user_agent=self.request.META.get("HTTP_USER_AGENT", "")[:255], successful=False,
                )
                recent_failures = user.login_history.filter(successful=False).order_by("-login_at")[:FAILED_LOGIN_LIMIT]
                if recent_failures.count() >= FAILED_LOGIN_LIMIT and all(not h.successful for h in recent_failures):
                    user.is_locked = True
                    user.save(update_fields=["is_locked"])
                    messages.error(self.request, "Too many failed attempts. This account is now locked.")
        return super().form_invalid(form)


class LogoutView(DjangoLogoutView):
    next_page = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            open_session = request.user.login_history.filter(logout_at__isnull=True).order_by("-login_at").first()
            if open_session:
                open_session.logout_at = timezone.now()
                open_session.save(update_fields=["logout_at"])
        return super().dispatch(request, *args, **kwargs)


@login_required
def logout_all_sessions(request):
    """Invalidate every other active session for this user by rotating their
    session auth hash — Django then rejects all previously issued session
    cookies for this account on their next request."""
    from django.contrib.auth import update_session_auth_hash
    update_session_auth_hash(request, request.user)
    messages.success(request, "You have been logged out of all other sessions.")
    return redirect("dashboard:home")


class ChangePasswordView(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/change_password.html"
    form_class = ForcedPasswordChangeForm
    success_url = reverse_lazy("dashboard:home")

    def form_valid(self, form):
        messages.success(self.request, "Password updated.")
        return super().form_valid(form)


class UserListView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    permission_required = "accounts.manage_users"
    paginate_by = 25

    def get_queryset(self):
        return User.objects.all().order_by("username")


@login_required
@permission_required("accounts.manage_users", raise_exception=True)
def create_user(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            temp_password = secrets.token_urlsafe(9)
            user = form.save(commit=False)
            user.set_password(temp_password)
            user.must_change_password = True
            user.created_by = request.user
            user.save()
            form.save_m2m()  # persists assigned_clients
            messages.success(
                request,
                f"{user.username} created with role {user.role_label}. "
                f"Temporary password (share securely, not via this screen in production): {temp_password}",
            )
            return redirect("accounts:user_list")
    else:
        form = UserCreateForm()
    return render(request, "accounts/user_form.html", {"form": form})


@login_required
@permission_required("accounts.manage_users", raise_exception=True)
def manage_user_clients(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserClientsForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Client assignments updated for {user.username}.")
            return redirect("accounts:user_list")
    else:
        form = UserClientsForm(instance=user)
    return render(request, "accounts/user_clients_form.html", {"form": form, "target_user": user})


@login_required
@permission_required("accounts.manage_users", raise_exception=True)
def admin_reset_password(request, pk):
    user = get_object_or_404(User, pk=pk)
    temp_password = secrets.token_urlsafe(9)
    user.set_password(temp_password)
    user.must_change_password = True
    user.is_locked = False
    user.save(update_fields=["password", "must_change_password", "is_locked"])
    messages.success(
        request,
        f"Password reset for {user.username}. Temporary password (share securely, not via this screen in production): {temp_password}",
    )
    return redirect("accounts:user_list")


@login_required
@permission_required("accounts.manage_users", raise_exception=True)
def toggle_user_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
    else:
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        messages.success(request, f"{user.username} is now {'active' if user.is_active else 'inactive'}.")
    return redirect("accounts:user_list")
