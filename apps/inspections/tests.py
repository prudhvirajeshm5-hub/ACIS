import io

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.masters.models import ConditionOption, InspectionItemMaster
from tests.factories import make_mis

from .models import Inspection, InspectionItemResult
from .services import bulk_save_checklist, start_inspection, submit_inspection

User = get_user_model()


class InspectionWorkflowTests(TestCase):
    def setUp(self):
        self.mis = make_mis()
        self.field_exec = User.objects.create_user(username="fe1", password="Str0ng!Passw0rd", role="field_executive")
        self.inspection = Inspection.objects.create(mis=self.mis, field_executive=self.field_exec)

    def test_start_inspection_moves_mis_to_in_progress(self):
        start_inspection(inspection=self.inspection, user=self.field_exec, latitude=18.52, longitude=73.85)
        self.mis.refresh_from_db()
        self.assertEqual(self.mis.inspection_stage, "in_progress")
        self.assertIsNotNone(self.inspection.status_history.filter(event__icontains="started").first())

    def test_submit_moves_mis_to_completed_and_qc_pending(self):
        submit_inspection(inspection=self.inspection, user=self.field_exec)
        self.mis.refresh_from_db()
        self.assertEqual(self.mis.inspection_stage, "completed")
        self.assertEqual(self.mis.qc_stage, "pending")
        self.assertTrue(self.inspection.is_submitted)

    def test_duplicate_submission_is_rejected(self):
        submit_inspection(inspection=self.inspection, user=self.field_exec)
        with self.assertRaises(PermissionDenied):
            submit_inspection(inspection=self.inspection, user=self.field_exec)

    def test_checklist_bulk_save_upserts_by_item(self):
        item = InspectionItemMaster.objects.first()
        safe = ConditionOption.objects.get(name="Safe")
        damaged = ConditionOption.objects.get(name="Damaged")

        bulk_save_checklist(
            inspection=self.inspection, result_model=InspectionItemResult, item_field="item",
            results=[{"item_id": item.id, "condition_id": safe.id, "remarks": ""}],
        )
        self.assertEqual(InspectionItemResult.objects.count(), 1)
        self.assertEqual(InspectionItemResult.objects.first().condition, safe)

        # Re-saving the same item updates rather than duplicates.
        bulk_save_checklist(
            inspection=self.inspection, result_model=InspectionItemResult, item_field="item",
            results=[{"item_id": item.id, "condition_id": damaged.id, "remarks": "Right fender dent"}],
        )
        self.assertEqual(InspectionItemResult.objects.count(), 1)
        self.assertEqual(InspectionItemResult.objects.first().condition, damaged)


class PhotoUploadValidationTests(TestCase):
    def setUp(self):
        self.mis = make_mis()
        self.field_exec = User.objects.create_user(username="fe2", password="Str0ng!Passw0rd", role="field_executive")
        self.inspection = Inspection.objects.create(mis=self.mis, field_executive=self.field_exec)

    def test_non_image_file_rejected_as_photo(self):
        from .models import InspectionPhoto
        fake_exe = SimpleUploadedFile("evil.exe", b"MZ\x90\x00fake-binary-content", content_type="application/octet-stream")
        photo = InspectionPhoto(inspection=self.inspection, category="front", file=fake_exe, uploaded_by=self.field_exec)
        with self.assertRaises(Exception):
            photo.full_clean()


class InspectionAccessControlTests(TestCase):
    def setUp(self):
        self.mis = make_mis()
        self.owner = User.objects.create_user(username="owner_fe", password="Str0ng!Passw0rd", role="field_executive")
        self.other = User.objects.create_user(username="other_fe", password="Str0ng!Passw0rd", role="field_executive")
        self.inspection = Inspection.objects.create(mis=self.mis, field_executive=self.owner)

    def test_field_executive_only_sees_own_inspections_via_api(self):
        self.client.login(username="other_fe", password="Str0ng!Passw0rd")
        response = self.client.get("/api/v1/inspections/")
        self.assertEqual(response.status_code, 200)
        ids = [row["id"] for row in response.json().get("results", response.json() if isinstance(response.json(), list) else [])]
        self.assertNotIn(str(self.inspection.pk), ids)

    def test_anonymous_cannot_reach_inspection_api(self):
        response = self.client.get("/api/v1/inspections/")
        self.assertEqual(response.status_code, 403)
