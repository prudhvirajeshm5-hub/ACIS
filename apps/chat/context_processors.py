from .services import unread_total


def chat_unread(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    return {"chat_unread": unread_total(user)}
