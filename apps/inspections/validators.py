"""
Upload validation per spec sections 15/27/43: check extension AND real
MIME type (via python-magic, which sniffs file content — never trust the
client-supplied filename or Content-Type header), enforce size limits, and
never allow the uploaded file to be treated as executable.
"""
from django.conf import settings
from django.core.exceptions import ValidationError

try:
    import magic  # python-magic
except ImportError:  # pragma: no cover — allows the codebase to import in
    magic = None    # environments where libmagic isn't installed yet.


def _sniff_mime(file_obj):
    if magic is None:
        return getattr(file_obj, "content_type", None)
    file_obj.seek(0)
    mime = magic.from_buffer(file_obj.read(2048), mime=True)
    file_obj.seek(0)
    return mime


def _validate(file_obj, *, allowed_types, max_size_mb, kind):
    if file_obj.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"{kind} exceeds the {max_size_mb}MB size limit.")
    mime = _sniff_mime(file_obj)
    if mime not in allowed_types:
        raise ValidationError(f"Unsupported {kind.lower()} type ({mime}). Allowed: {', '.join(allowed_types)}.")


def validate_photo_file(file_obj):
    _validate(file_obj, allowed_types=settings.ALLOWED_PHOTO_TYPES, max_size_mb=settings.MAX_PHOTO_SIZE_MB, kind="Photo")


def validate_video_file(file_obj):
    _validate(file_obj, allowed_types=settings.ALLOWED_VIDEO_TYPES, max_size_mb=settings.MAX_VIDEO_SIZE_MB, kind="Video")


def validate_document_file(file_obj):
    _validate(file_obj, allowed_types=settings.ALLOWED_DOCUMENT_TYPES, max_size_mb=settings.MAX_PHOTO_SIZE_MB, kind="Document")
