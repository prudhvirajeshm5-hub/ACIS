from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from apps.accounts.viewsets import UserViewSet
from apps.customers.viewsets import CustomerViewSet
from apps.inspections.viewsets import InspectionVideoViewSet, InspectionViewSet, secure_video_view
from apps.insurers.viewsets import InsuranceBranchViewSet, InsuranceCompanyViewSet
from apps.masters.viewsets import (
    AccessoryMasterViewSet, CityViewSet, ConditionOptionViewSet, DistrictViewSet,
    GlassItemMasterViewSet, InspectionItemMasterViewSet, PhotoCategoryMasterViewSet, StateViewSet,
    VehicleMakeViewSet, VehicleModelViewSet, VehicleTypeViewSet, VideoCategoryMasterViewSet,
)
from apps.mis.viewsets import MISViewSet
from apps.qc.viewsets import QCReviewViewSet
from apps.vehicles.viewsets import VehicleViewSet

from .views import DashboardStatsAPIView

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("companies", InsuranceCompanyViewSet, basename="insurancecompany")
router.register("branches", InsuranceBranchViewSet, basename="insurancebranch")
router.register("customers", CustomerViewSet, basename="customer")
router.register("vehicles", VehicleViewSet, basename="vehicle")
router.register("mis", MISViewSet, basename="mis")
router.register("inspections", InspectionViewSet, basename="inspection")
router.register("inspections/videos", InspectionVideoViewSet, basename="inspectionvideo")
router.register("qc-reviews", QCReviewViewSet, basename="qcreview")

# Masters
router.register("masters/states", StateViewSet, basename="state")
router.register("masters/districts", DistrictViewSet, basename="district")
router.register("masters/cities", CityViewSet, basename="city")
router.register("masters/vehicle-types", VehicleTypeViewSet, basename="vehicletype")
router.register("masters/vehicle-makes", VehicleMakeViewSet, basename="vehiclemake")
router.register("masters/vehicle-models", VehicleModelViewSet, basename="vehiclemodel")
router.register("masters/inspection-items", InspectionItemMasterViewSet, basename="inspectionitemmaster")
router.register("masters/glass-items", GlassItemMasterViewSet, basename="glassitemmaster")
router.register("masters/accessories", AccessoryMasterViewSet, basename="accessorymaster")
router.register("masters/conditions", ConditionOptionViewSet, basename="conditionoption")
router.register("masters/video-categories", VideoCategoryMasterViewSet, basename="videocategorymaster")
router.register("masters/photo-categories", PhotoCategoryMasterViewSet, basename="photocategorymaster")

urlpatterns = [
    path("auth/token/", obtain_auth_token, name="api_token_auth"),
    path("dashboard/", DashboardStatsAPIView.as_view(), name="api_dashboard"),
    path("inspections/videos/<uuid:video_id>/secure/", secure_video_view, name="secure_video"),
    path("", include(router.urls)),
]
