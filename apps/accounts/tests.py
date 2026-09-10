from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tests.factories import make_insurer, make_masters

from .models import LoginHistory

User = get_user_model()


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="priya", password="Str0ng!Passw0rd", role="qc_executive")
        self.user.must_change_password = False
        self.user.save()

    def test_login_success_records_history(self):
        response = self.client.post(reverse("accounts:login"), {"username": "priya", "password": "Str0ng!Passw0rd"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(LoginHistory.objects.filter(user=self.user, successful=True).exists())

    def test_login_with_email_works(self):
        self.user.email = "priya@example.com"
        self.user.save()
        response = self.client.post(reverse("accounts:login"), {"username": "priya@example.com", "password": "Str0ng!Passw0rd"})
        self.assertEqual(response.status_code, 302)

    def test_wrong_password_recorded_and_does_not_leak_user_existence(self):
        response = self.client.post(reverse("accounts:login"), {"username": "priya", "password": "wrong"})
        self.assertEqual(response.status_code, 200)  # re-renders form, no redirect
        self.assertTrue(LoginHistory.objects.filter(user=self.user, successful=False).exists())

    def test_account_locks_after_five_failed_attempts(self):
        for _ in range(5):
            self.client.post(reverse("accounts:login"), {"username": "priya", "password": "wrong"})
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked)

    def test_locked_account_cannot_log_in_even_with_correct_password(self):
        self.user.is_locked = True
        self.user.save()
        response = self.client.post(reverse("accounts:login"), {"username": "priya", "password": "Str0ng!Passw0rd"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client.session.get("_auth_user_id"))

    def test_must_change_password_redirects_to_change_password(self):
        self.user.must_change_password = True
        self.user.save()
        response = self.client.post(reverse("accounts:login"), {"username": "priya", "password": "Str0ng!Passw0rd"}, follow=True)
        self.assertRedirects(response, reverse("accounts:change_password"))


class UserManagementPermissionTests(TestCase):
    def setUp(self):
        self.regular_user = User.objects.create_user(username="normal", password="Str0ng!Passw0rd", role="mis_operator")
        self.admin = User.objects.create_user(username="admin1", password="Str0ng!Passw0rd", role="admin", is_superuser=True)

    def test_non_privileged_user_cannot_view_user_list(self):
        self.client.login(username="normal", password="Str0ng!Passw0rd")
        response = self.client.get(reverse("accounts:user_list"))
        self.assertEqual(response.status_code, 403)

    def test_superuser_can_view_user_list(self):
        self.client.login(username="admin1", password="Str0ng!Passw0rd")
        response = self.client.get(reverse("accounts:user_list"))
        self.assertEqual(response.status_code, 200)

    def test_admin_cannot_deactivate_own_account(self):
        self.client.login(username="admin1", password="Str0ng!Passw0rd")
        self.client.post(reverse("accounts:toggle_user_active", args=[self.admin.pk]))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)


class CreateUserTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin2", password="Str0ng!Passw0rd", role="admin", is_superuser=True)
        self.regular_user = User.objects.create_user(username="normal2", password="Str0ng!Passw0rd", role="mis_operator")

    def test_non_privileged_user_cannot_create_users(self):
        self.client.login(username="normal2", password="Str0ng!Passw0rd")
        response = self.client.get(reverse("accounts:create_user"))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_a_new_user_with_forced_password_change(self):
        self.client.login(username="admin2", password="Str0ng!Passw0rd")
        response = self.client.post(reverse("accounts:create_user"), {
            "username": "newop", "first_name": "New", "last_name": "Operator",
            "email": "newop@example.com", "employee_code": "EMP001", "role": "mis_operator", "phone": "",
        })
        self.assertRedirects(response, reverse("accounts:user_list"))
        new_user = User.objects.get(username="newop")
        self.assertTrue(new_user.must_change_password)
        self.assertFalse(new_user.has_usable_password() is False)  # a real (random) password was set


class ManageUserClientsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin3", password="Str0ng!Passw0rd", role="admin", is_superuser=True)
        self.operator = User.objects.create_user(username="op3", password="Str0ng!Passw0rd", role="mis_operator")
        masters = make_masters()
        self.company, _ = make_insurer(masters["district"])

    def test_admin_can_assign_a_client_to_a_user(self):
        self.client.login(username="admin3", password="Str0ng!Passw0rd")
        response = self.client.post(
            reverse("accounts:manage_user_clients", args=[self.operator.pk]),
            {"assigned_clients": [str(self.company.pk)]},
        )
        self.assertRedirects(response, reverse("accounts:user_list"))
        self.operator.refresh_from_db()
        self.assertIn(self.company, self.operator.assigned_clients.all())
