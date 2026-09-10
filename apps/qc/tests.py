from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.inspections.models import Inspection
from tests.factories import make_mis

from .models import QCDecision, QCReview
from .services import record_qc_decision

User = get_user_model()


class QCDecisionTests(TestCase):
    def setUp(self):
        self.mis = make_mis()
        self.field_exec = User.objects.create_user(username="fe1", password="Str0ng!Passw0rd", role="field_executive")
        self.qc_exec = User.objects.create_user(username="qc1", password="Str0ng!Passw0rd", role="qc_executive")
        self.inspection = Inspection.objects.create(mis=self.mis, field_executive=self.field_exec, is_submitted=True)
        self.mis.qc_stage = "pending"
        self.mis.save()

    def test_recommended_decision_approves_mis(self):
        record_qc_decision(inspection=self.inspection, qc_executive=self.qc_exec, decision=QCDecision.RECOMMENDED, remarks="Looks good")
        self.mis.refresh_from_db()
        self.assertEqual(self.mis.qc_stage, "approved")

    def test_need_correction_reopens_inspection_for_resubmission(self):
        record_qc_decision(inspection=self.inspection, qc_executive=self.qc_exec, decision=QCDecision.NEED_CORRECTION, remarks="Fix glass section")
        self.mis.refresh_from_db()
        self.inspection.refresh_from_db()
        self.assertEqual(self.mis.qc_stage, "correction")
        self.assertFalse(self.inspection.is_submitted)

    def test_review_history_is_preserved_not_overwritten(self):
        record_qc_decision(inspection=self.inspection, qc_executive=self.qc_exec, decision=QCDecision.NEED_CORRECTION, remarks="First pass")
        record_qc_decision(inspection=self.inspection, qc_executive=self.qc_exec, decision=QCDecision.RECOMMENDED, remarks="Second pass, approved")
        self.assertEqual(QCReview.objects.filter(inspection=self.inspection).count(), 2)
        latest = QCReview.objects.filter(inspection=self.inspection).order_by("-reviewed_at").first()
        self.assertIsNotNone(latest.supersedes)

    def test_qc_review_records_are_read_only_in_admin(self):
        from django.contrib import admin
        self.assertFalse(admin.site._registry[QCReview].has_change_permission(None))
        self.assertFalse(admin.site._registry[QCReview].has_delete_permission(None))
