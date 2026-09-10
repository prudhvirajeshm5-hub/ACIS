"""
Plain helper functions rather than factory_boy factories, so the test
suite has zero extra dependency beyond Django itself and pytest-django.
Swap these for real Factory classes as the test suite grows.
"""
from django.contrib.auth import get_user_model

from apps.customers.models import Customer
from apps.insurers.models import InsuranceBranch, InsuranceCompany
from apps.masters.models import (
    ConditionOption, District, FuelType, GlassItemMaster, InspectionItemMaster,
    State, VehicleMake, VehicleModel, VehicleType, VideoCategoryMaster,
)
from apps.mis.models import MIS
from apps.vehicles.models import Vehicle

User = get_user_model()


def make_user(username="testuser", role="mis_operator", **kwargs):
    user = User.objects.create_user(username=username, password="Str0ng!Passw0rd", role=role, **kwargs)
    return user


def make_masters():
    state = State.objects.create(name="Maharashtra")
    district = District.objects.create(state=state, name="Pune")
    vt = VehicleType.objects.create(name="Hatchback")
    make = VehicleMake.objects.create(vehicle_type=vt, name="Maruti Suzuki")
    model = VehicleModel.objects.create(make=make, name="Swift")
    fuel = FuelType.objects.create(name="Petrol")
    ConditionOption.objects.get_or_create(name="Safe", defaults={"is_positive": True})
    ConditionOption.objects.get_or_create(name="Damaged", defaults={"is_positive": False})
    InspectionItemMaster.objects.get_or_create(name="Front Bumper")
    GlassItemMaster.objects.get_or_create(name="Front Windshield")
    VideoCategoryMaster.objects.get_or_create(name="Exterior Walkaround")
    return {"state": state, "district": district, "vehicle_type": vt, "make": make, "model": model, "fuel": fuel}


def make_insurer(district):
    company = InsuranceCompany.objects.create(name="Bajaj Allianz", code="BAJ")
    branch = InsuranceBranch.objects.create(company=company, name="Pune Camp", district=district)
    return company, branch


def make_customer_and_vehicle(masters):
    customer = Customer.objects.create(name="Ramesh Iyer", mobile="9845022310", district=masters["district"])
    vehicle = Vehicle.objects.create(
        registration_number="MH12AB1234", vehicle_type=masters["vehicle_type"],
        make=masters["make"], model=masters["model"], fuel_type=masters["fuel"],
        manufacturing_year=2022, owner=customer,
    )
    return customer, vehicle


def make_mis(**overrides):
    masters = make_masters()
    company, branch = make_insurer(masters["district"])
    customer, vehicle = make_customer_and_vehicle(masters)
    defaults = dict(
        mis_date="2026-09-07", insurance_company=company, branch=branch,
        customer=customer, vehicle=vehicle,
    )
    defaults.update(overrides)
    return MIS.objects.create(**defaults)
