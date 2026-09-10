from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import InsuranceCompany

User = get_user_model()


class AddClientTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin4", password="Str0ng!Passw0rd", role="admin", is_superuser=True)
        self.operator = User.objects.create_user(username="op4", password="Str0ng!Passw0rd", role="mis_operator")

    def test_admin_can_add_a_client(self):
        self.client.login(username="admin4", password="Str0ng!Passw0rd")
        response = self.client.post(reverse("insurers:create"), {
            "name": "Reliance General", "code": "REL", "gstin": "", "contact_email": "", "contact_phone": "",
        })
        self.assertRedirects(response, reverse("insurers:list"))
        self.assertTrue(InsuranceCompany.objects.filter(code="REL").exists())

    def test_mis_operator_cannot_add_a_client(self):
        self.client.login(username="op4", password="Str0ng!Passw0rd")
        response = self.client.get(reverse("insurers:create"))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_view_client_list(self):
        response = self.client.get(reverse("insurers:list"))
        self.assertEqual(response.status_code, 302)
