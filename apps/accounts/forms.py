from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username or email",
        widget=forms.TextInput(attrs={"autofocus": True, "class": "input", "placeholder": "you@company.com"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "input", "placeholder": "••••••••••"})
    )
    remember_me = forms.BooleanField(required=False, initial=True)

    error_messages = {
        **AuthenticationForm.error_messages,
        "inactive": "This account has been deactivated. Contact your administrator.",
    }


class ForcedPasswordChangeForm(SetPasswordForm):
    """Used when must_change_password is True (first login, or after an admin reset)."""

    def save(self, commit=True):
        user = super().save(commit=False)
        user.must_change_password = False
        if commit:
            user.save()
        return user


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "employee_code", "role", "phone", "is_active"]
        widgets = {f: forms.TextInput(attrs={"class": "input"}) for f in
                   ["username", "first_name", "last_name", "email", "employee_code", "phone"]}


class UserCreateForm(forms.ModelForm):
    """
    No password field here — creating a user always issues a random
    temporary password and forces a change at first login, the same flow
    admin_reset_password already uses for existing users. That way there's
    exactly one place (views.py) that generates and displays a temp
    password, instead of two slightly different flows.
    """
    assigned_clients = forms.ModelMultipleChoiceField(
        queryset=None, required=False, widget=forms.SelectMultiple(attrs={"class": "input", "size": 6}),
        help_text="Only used for the MIS Operator role — restricts which insurance companies this user can see and work with. Leave empty for roles that should see everything.",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "employee_code", "role", "phone"]
        widgets = {f: forms.TextInput(attrs={"class": "input"}) for f in
                   ["username", "first_name", "last_name", "email", "employee_code", "phone"]}
        widgets["role"] = forms.Select(attrs={"class": "input"})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.insurers.models import InsuranceCompany
        self.fields["assigned_clients"].queryset = InsuranceCompany.objects.filter(active=True)


class UserClientsForm(forms.ModelForm):
    """Standalone form for the 'assign clients to a user' action, kept
    separate from the full user-edit form so it's a one-click, single-purpose
    screen reachable straight from the user list."""
    class Meta:
        model = User
        fields = ["assigned_clients"]
        widgets = {"assigned_clients": forms.SelectMultiple(attrs={"class": "input", "size": 10})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.insurers.models import InsuranceCompany
        self.fields["assigned_clients"].queryset = InsuranceCompany.objects.filter(active=True)
        self.fields["assigned_clients"].label = "Assigned clients (insurance companies)"
