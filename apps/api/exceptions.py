"""
One consistent error shape across the whole API, per spec section 23
("Consistent error responses"):

    {"detail": "...", "code": "...", "fields": {...}}

so a Flutter client (or any consumer) can branch on `code` without parsing
human-readable text.
"""
from rest_framework.views import exception_handler


def consistent_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    data = response.data
    if isinstance(data, dict) and "detail" in data and len(data) == 1:
        payload = {"detail": str(data["detail"]), "code": getattr(exc, "default_code", "error")}
    elif isinstance(data, dict):
        payload = {"detail": "Validation failed.", "code": "validation_error", "fields": data}
    else:
        payload = {"detail": str(data), "code": "error"}

    response.data = payload
    return response
