from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.insurers.models import InsuranceBranch, InsuranceCompany
from tests.factories import make_customer_and_vehicle, make_insurer, make_masters

from .models import MIS, MISInspectionStage
from .services import assign_field_executive, create_mis

User = get_user_model()


class MISCreationTests(TestCase):
    def setUp(self):
        self.masters = make_masters()
        self.company, self.branch = make_insurer(self.masters["district"])
        self.customer, self.vehicle = make_customer_and_vehicle(self.masters)
        self.operator = User.objects.create_user(username="op1", password="Str0ng!Passw0rd", role="mis_operator")

    def test_mis_number_is_generated_sequentially(self):
        mis1 = create_mis(data=dict(
            mis_date="2026-09-07", insurance_company=self.company, branch=self.branch,
            customer=self.customer, vehicle=self.vehicle,
        ), created_by=self.operator)
        mis2 = create_mis(data=dict(
            mis_date="2026-09-07", insurance_company=self.company, branch=self.branch,
            customer=self.customer, vehicle=self.vehicle,
        ), created_by=self.operator)
        self.assertTrue(mis1.mis_number.startswith("MIS-"))
        self.assertNotEqual(mis1.mis_number, mis2.mis_number)
        seq1 = int(mis1.mis_number.rsplit("-", 1)[-1])
        seq2 = int(mis2.mis_number.rsplit("-", 1)[-1])
        self.assertEqual(seq2, seq1 + 1)

    def test_new_mis_defaults_to_pending_and_not_started_qc(self):
        mis = create_mis(data=dict(
            mis_date="2026-09-07", insurance_company=self.company, branch=self.branch,
            customer=self.customer, vehicle=self.vehicle,
        ), created_by=self.operator)
        self.assertEqual(mis.inspection_stage, MISInspectionStage.PENDING)
        self.assertEqual(mis.qc_stage, "not_started")


class MISAssignmentTests(TestCase):
    def setUp(self):
        self.masters = make_masters()
        self.company, self.branch = make_insurer(self.masters["district"])
        self.customer, self.vehicle = make_customer_and_vehicle(self.masters)
        self.field_exec = User.objects.create_user(username="fe1", password="Str0ng!Passw0rd", role="field_executive")
        self.mis = MIS.objects.create(
            mis_date="2026-09-07", insurance_company=self.company, branch=self.branch,
            customer=self.customer, vehicle=self.vehicle,
        )

    def test_assigning_creates_an_inspection_and_updates_stage(self):
        assign_field_executive(mis=self.mis, field_executive=self.field_exec, scheduled_date="2026-09-09", assigned_by=self.field_exec)
        self.mis.refresh_from_db()
        self.assertEqual(self.mis.inspection_stage, MISInspectionStage.ASSIGNED)
        self.assertEqual(self.mis.field_executive, self.field_exec)
        self.assertTrue(hasattr(self.mis, "inspection"))


class MISListViewPermissionTests(TestCase):
    def setUp(self):
        self.reader = User.objects.create_user(username="reader", password="Str0ng!Passw0rd", role="read_only")

    def test_authenticated_user_can_view_mis_list(self):
        self.client.login(username="reader", password="Str0ng!Passw0rd")
        response = self.client.get("/mis/")
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get("/mis/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)


class ClientScopingTests(TestCase):
    """Covers the 'assign clients to users' feature: MIS Operators should
    only see MIS for their assigned insurance companies; every other role
    sees everything regardless of assigned_clients."""

    def setUp(self):
        self.masters = make_masters()
        self.company_a, self.branch_a = make_insurer(self.masters["district"])
        self.company_b = InsuranceCompany.objects.create(name="ICICI Lombard", code="ICI")
        self.branch_b = InsuranceBranch.objects.create(company=self.company_b, name="Pune Kothrud", district=self.masters["district"])
        self.customer, self.vehicle = make_customer_and_vehicle(self.masters)

        self.mis_a = MIS.objects.create(mis_date="2026-09-07", insurance_company=self.company_a, branch=self.branch_a, customer=self.customer, vehicle=self.vehicle)
        self.mis_b = MIS.objects.create(mis_date="2026-09-07", insurance_company=self.company_b, branch=self.branch_b, customer=self.customer, vehicle=self.vehicle)

    def test_unscoped_mis_operator_sees_no_mis(self):
        operator = User.objects.create_user(username="op_unscoped", password="Str0ng!Passw0rd", role="mis_operator")
        visible = list(operator.visible_insurance_companies())
        self.assertEqual(visible, [])

    def test_scoped_mis_operator_sees_only_assigned_company(self):
        operator = User.objects.create_user(username="op_scoped", password="Str0ng!Passw0rd", role="mis_operator")
        operator.assigned_clients.add(self.company_a)
        visible_ids = set(operator.visible_insurance_companies().values_list("id", flat=True))
        self.assertEqual(visible_ids, {self.company_a.id})

    def test_mis_list_view_respects_scoping_for_mis_operator(self):
        operator = User.objects.create_user(username="op_view", password="Str0ng!Passw0rd", role="mis_operator")
        operator.assigned_clients.add(self.company_a)
        self.client.login(username="op_view", password="Str0ng!Passw0rd")
        response = self.client.get("/mis/")
        mis_numbers = [m.mis_number for m in response.context["mis_records"]]
        self.assertIn(self.mis_a.mis_number, mis_numbers)
        self.assertNotIn(self.mis_b.mis_number, mis_numbers)

    def test_manager_role_is_not_scoped_even_with_assignments(self):
        manager = User.objects.create_user(username="mgr1", password="Str0ng!Passw0rd", role="manager")
        # Assigning clients to a non-scoped role should have no restrictive effect.
        manager.assigned_clients.add(self.company_a)
        visible_ids = set(manager.visible_insurance_companies().values_list("id", flat=True))
        self.assertIn(self.company_b.id, visible_ids)

    def test_superuser_bypasses_scoping_regardless_of_role(self):
        su = User.objects.create_user(username="su1", password="Str0ng!Passw0rd", role="mis_operator", is_superuser=True)
        visible_ids = set(su.visible_insurance_companies().values_list("id", flat=True))
        self.assertIn(self.company_a.id, visible_ids)
        self.assertIn(self.company_b.id, visible_ids)
