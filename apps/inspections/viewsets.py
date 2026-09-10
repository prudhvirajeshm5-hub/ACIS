from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.http import FileResponse, Http404
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit.utils import log_action

from .models import (
    Inspection, InspectionAccessoryResult, InspectionDocument, InspectionGlassResult,
    InspectionItemResult, InspectionPhoto, InspectionVideo, PreviousInsurance,
)
from .services import add_photo, add_video, submit_inspection

video_link_signer = TimestampSigner(salt="inspection-video-access")
VIDEO_LINK_MAX_AGE_SECONDS = 60 * 30  # 30 minutes — QR codes point at a URL that expires, per spec


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------
class InspectionItemResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionItemResult
        fields = ["id", "item", "condition", "remarks"]


class InspectionGlassResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionGlassResult
        fields = ["id", "item", "condition", "remarks"]


class InspectionAccessoryResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionAccessoryResult
        fields = ["id", "item", "present", "condition", "remarks"]


class PreviousInsuranceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreviousInsurance
        fields = "__all__"
        read_only_fields = ["id", "inspection"]


class InspectionDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionDocument
        fields = ["id", "document_type", "file", "verified", "verified_by", "verified_at"]
        read_only_fields = ["id", "verified_by", "verified_at"]


class InspectionPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionPhoto
        fields = [
            "id", "category", "original_filename", "file", "file_size", "mime_type",
            "uploaded_by", "uploaded_at", "capture_datetime", "latitude", "longitude", "sequence",
        ]
        read_only_fields = ["id", "original_filename", "file_size", "mime_type", "uploaded_by", "uploaded_at"]


class InspectionVideoSerializer(serializers.ModelSerializer):
    secure_view_url = serializers.SerializerMethodField()

    class Meta:
        model = InspectionVideo
        fields = [
            "id", "category", "title", "original_filename", "file", "thumbnail", "mime_type",
            "file_size", "duration_seconds", "width", "height", "capture_datetime",
            "uploaded_by", "uploaded_at", "latitude", "longitude", "location_name",
            "description", "sequence", "processing_status", "active", "secure_view_url",
        ]
        read_only_fields = [
            "id", "original_filename", "file_size", "mime_type", "uploaded_by", "uploaded_at",
            "processing_status", "duration_seconds", "width", "height",
        ]

    def get_secure_view_url(self, obj):
        """Never expose the raw storage path — always a signed, time-limited
        application URL, exactly as the spec requires for the QR code."""
        token = video_link_signer.sign(str(obj.id))
        request = self.context.get("request")
        path = f"/api/v1/inspections/videos/{obj.id}/secure/?token={token}"
        return request.build_absolute_uri(path) if request else path


class InspectionSerializer(serializers.ModelSerializer):
    mis_number = serializers.CharField(source="mis.mis_number", read_only=True)
    item_results = InspectionItemResultSerializer(many=True, read_only=True)
    glass_results = InspectionGlassResultSerializer(many=True, read_only=True)
    accessory_results = InspectionAccessoryResultSerializer(many=True, read_only=True)
    photos = InspectionPhotoSerializer(many=True, read_only=True)
    videos = InspectionVideoSerializer(many=True, read_only=True)
    documents = InspectionDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Inspection
        fields = [
            "id", "mis", "mis_number", "field_executive", "accepted_at", "started_at", "submitted_at",
            "odometer_reading", "engine_condition", "latitude", "longitude", "is_submitted",
            "item_results", "glass_results", "accessory_results", "photos", "videos", "documents",
        ]
        read_only_fields = ["id", "accepted_at", "started_at", "submitted_at", "is_submitted"]


# ---------------------------------------------------------------------------
# Viewsets
# ---------------------------------------------------------------------------
class InspectionViewSet(viewsets.ModelViewSet):
    queryset = Inspection.objects.select_related("mis", "field_executive").prefetch_related(
        "item_results", "glass_results", "accessory_results", "photos", "videos", "documents"
    )
    serializer_class = InspectionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["field_executive", "is_submitted"]

    def get_queryset(self):
        """Field executives only ever see their own assignments through the
        API — enforced here, not just hidden in the UI, since this is the
        same endpoint the future Flutter app will call directly."""
        qs = super().get_queryset()
        user = self.request.user
        if user.role == "field_executive" and not user.is_superuser:
            return qs.filter(field_executive=user)
        return qs

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        inspection = self.get_object()
        submit_inspection(inspection=inspection, user=request.user)
        return Response(self.get_serializer(inspection).data)

    @action(detail=True, methods=["post"], url_path="photos")
    def upload_photo_action(self, request, pk=None):
        """Single-slot upload for the mobile app: `category` is a
        PhotoCategoryMaster id. Re-uploading a mandatory slot replaces its
        photo; the non-mandatory 'Additional Photos' slot is capped at
        `category.max_count` here too, matching the bulk web upload."""
        inspection = self.get_object()
        if not request.user.has_perm("inspections.upload_photo"):
            return Response({"detail": "Not permitted."}, status=403)
        file = request.FILES.get("file")
        category_id = request.data.get("category")
        if not file or not category_id:
            return Response({"detail": "file and category are required"}, status=400)
        from apps.masters.models import PhotoCategoryMaster
        try:
            category = PhotoCategoryMaster.objects.get(pk=category_id, active=True)
        except PhotoCategoryMaster.DoesNotExist:
            return Response({"detail": "Unknown photo category."}, status=400)
        if category.is_mandatory:
            InspectionPhoto.objects.filter(inspection=inspection, category=category).delete()
        elif inspection.photos.filter(category=category).count() >= category.max_count:
            return Response(
                {"detail": f"Only {category.max_count} \"{category.name}\" photo(s) allowed."}, status=400
            )
        photo = add_photo(inspection=inspection, file=file, category=category, uploaded_by=request.user)
        return Response(InspectionPhotoSerializer(photo).data, status=201)

    @action(detail=True, methods=["post"], url_path="videos")
    def upload_video_action(self, request, pk=None):
        inspection = self.get_object()
        if not request.user.has_perm("inspections.upload_video"):
            return Response({"detail": "Not permitted."}, status=403)
        file = request.FILES.get("file")
        category_id = request.data.get("category")
        if not file or not category_id:
            return Response({"detail": "file and category are required"}, status=400)
        from apps.masters.models import VideoCategoryMaster
        category = VideoCategoryMaster.objects.get(pk=category_id)
        video = add_video(inspection=inspection, file=file, category=category, uploaded_by=request.user)
        return Response(InspectionVideoSerializer(video, context={"request": request}).data, status=201)


class InspectionVideoViewSet(viewsets.ReadOnlyModelViewSet):
    """Direct video listing/detail (as distinct from the nested actions
    above) so /api/v1/inspections/{id}/videos/ and
    /api/v1/inspections/videos/{video_id}/ from the spec both exist."""
    queryset = InspectionVideo.objects.filter(active=True).select_related("inspection", "category")
    serializer_class = InspectionVideoSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["get"])
    def stream(self, request, pk=None):
        video = self.get_object()
        self._check_object_access(request, video)
        log_action(action="download", module="inspections", obj=video)
        return FileResponse(video.file.open("rb"), content_type=video.mime_type)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        video = self.get_object()
        self._check_object_access(request, video)
        log_action(action="download", module="inspections", obj=video)
        response = FileResponse(video.file.open("rb"), as_attachment=True, filename=video.original_filename)
        return response

    def _check_object_access(self, request, video):
        """Object-level check beyond DRF's default model permissions: a
        field executive may only stream/download videos from their own
        inspections, per the spec's 'prevent unauthorized users from
        accessing another inspection's videos' requirement."""
        user = request.user
        if user.is_superuser or user.role in ("super_admin", "admin", "manager", "qc_executive"):
            return
        if video.inspection.field_executive_id != user.id:
            raise Http404()


from django.contrib.auth.decorators import login_required


@login_required
def secure_video_view(request, video_id):
    """
    The endpoint a QR code in the PDF report actually points to:
    /reports/{report_id}/videos/{video_id}/ in the spec, implemented here as
    a signed, time-limited link so the raw storage path is never exposed.
    Still requires the user to be authenticated, per spec section on QR
    code video access.
    """
    token = request.GET.get("token", "")
    try:
        unsigned_id = video_link_signer.unsign(token, max_age=VIDEO_LINK_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        raise Http404("This video link has expired or is invalid.")
    if unsigned_id != str(video_id):
        raise Http404()
    video = InspectionVideo.objects.filter(id=video_id, active=True).first()
    if not video:
        raise Http404()
    log_action(action="download", module="inspections", obj=video, new_value={"via": "qr_secure_link"})
    return FileResponse(video.file.open("rb"), content_type=video.mime_type)
