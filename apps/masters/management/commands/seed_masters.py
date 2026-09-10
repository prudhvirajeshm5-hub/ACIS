"""
Populates the minimum master data needed for the app to be usable out of
the box: states/districts, a couple of vehicle types/makes/models, the
standard condition options, the body/glass/accessory checklists from the
spec, and video categories. Idempotent — safe to re-run.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.masters import models as m

CONDITIONS = [
    ("Safe", True), ("Damaged", False), ("Scratched", False), ("Dent", False),
    ("Broken", False), ("Repaired", False), ("Replaced", False),
    ("Not Available", True), ("Not Applicable", True),
]

BODY_ITEMS = [
    "Front Bumper", "Rear Bumper", "Bonnet", "Roof", "Front Panel", "Rear Panel",
    "Left Fender", "Right Fender", "Front Left Door", "Front Right Door",
    "Rear Left Door", "Rear Right Door", "Left Quarter Panel", "Right Quarter Panel",
    "Pillars", "Running Board", "Boot", "Grill", "Head Lamps", "Tail Lamps",
    "Fog Lamps", "ORVM", "AC Condenser", "Radiator",
]

GLASS_ITEMS = [
    "Front Windshield", "Rear Windshield", "Front Left Glass", "Front Right Glass",
    "Rear Left Glass", "Rear Right Glass", "Quarter Glass", "Sunroof Glass",
]

ACCESSORY_ITEMS = [
    "AC", "Music System", "Reverse Camera", "Parking Sensors", "Alloy Wheels",
    "Spare Wheel", "Jack", "Tool Kit", "Seat Covers", "Floor Mats",
    "Central Locking", "Power Windows",
]

PHOTO_CATEGORIES = [
    "Front View", "Rear View", "Left Side View", "Right Side View",
    "Front-Left 45°", "Front-Right 45°", "Rear-Left 45°", "Rear-Right 45°",
    "Engine Bay", "Dashboard / Odometer", "Chassis Number / VIN Plate",
    "Number Plate (Front)", "Number Plate (Rear)", "Roof / Interior",
]  # 14 mandatory bulk-upload slots — one photo each, re-upload replaces it.

VIDEO_CATEGORIES = [
    "Exterior Walkaround", "Front View", "Rear View", "Left Side", "Right Side",
    "Engine Bay", "Interior", "Odometer", "Chassis / VIN", "Damage Evidence",
    "Document Verification", "Test Drive", "Other",
]

STATES_DISTRICTS = {
    "Maharashtra": ["Pune", "Mumbai", "Nagpur"],
    "Karnataka": ["Bengaluru Urban", "Mysuru"],
}

VEHICLE_TYPES = {
    "Hatchback": {"Maruti Suzuki": ["Swift", "Baleno"], "Hyundai": ["i20", "Grand i10"]},
    "Sedan": {"Honda": ["City"], "Hyundai": ["Verna"]},
    "SUV": {"Tata": ["Nexon", "Harrier"], "Mahindra": ["XUV700"], "Kia": ["Seltos"]},
}

FUEL_TYPES = ["Petrol", "Diesel", "CNG", "Electric"]
PAYMENT_MODES = ["Cash", "NEFT", "UPI", "Cheque"]


class Command(BaseCommand):
    help = "Seed minimum viable master data so the app is usable out of the box."

    @transaction.atomic
    def handle(self, *args, **options):
        for name, is_positive in CONDITIONS:
            m.ConditionOption.objects.get_or_create(name=name, defaults={"is_positive": is_positive})

        for i, name in enumerate(BODY_ITEMS):
            m.InspectionItemMaster.objects.get_or_create(name=name, defaults={"display_order": i})
        for i, name in enumerate(GLASS_ITEMS):
            m.GlassItemMaster.objects.get_or_create(name=name, defaults={"display_order": i})
        for i, name in enumerate(ACCESSORY_ITEMS):
            m.AccessoryMaster.objects.get_or_create(name=name, defaults={"display_order": i})
        for i, name in enumerate(VIDEO_CATEGORIES):
            m.VideoCategoryMaster.objects.get_or_create(name=name, defaults={"display_order": i})

        for i, name in enumerate(PHOTO_CATEGORIES):
            m.PhotoCategoryMaster.objects.get_or_create(
                name=name, defaults={"display_order": i, "is_mandatory": True, "max_count": 1}
            )
        m.PhotoCategoryMaster.objects.get_or_create(
            name="Additional Photos",
            defaults={"display_order": len(PHOTO_CATEGORIES), "is_mandatory": False, "max_count": 4},
        )

        for state_name, districts in STATES_DISTRICTS.items():
            state, _ = m.State.objects.get_or_create(name=state_name)
            for d in districts:
                m.District.objects.get_or_create(state=state, name=d)

        for vt_name, makes in VEHICLE_TYPES.items():
            vt, _ = m.VehicleType.objects.get_or_create(name=vt_name)
            for make_name, models_ in makes.items():
                make, _ = m.VehicleMake.objects.get_or_create(vehicle_type=vt, name=make_name)
                for model_name in models_:
                    m.VehicleModel.objects.get_or_create(make=make, name=model_name)

        for name in FUEL_TYPES:
            m.FuelType.objects.get_or_create(name=name)
        for name in PAYMENT_MODES:
            m.PaymentMode.objects.get_or_create(name=name)

        for i, name in enumerate(["Pending", "Assigned", "In Progress", "Completed"]):
            m.InspectionStatus.objects.get_or_create(name=name, defaults={"sequence": i})
        for i, name in enumerate(["Not Started", "Pending", "Approved", "Rejected", "Correction"]):
            m.QCStatus.objects.get_or_create(name=name, defaults={"sequence": i})
        for name in ["Open", "In Progress", "Closed"]:
            m.TicketStatus.objects.get_or_create(name=name)

        self.stdout.write(self.style.SUCCESS("Master data seeded."))
