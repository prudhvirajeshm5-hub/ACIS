import threading

_thread_locals = threading.local()


class AuditContextMiddleware:
    """
    Stashes the current request's user/IP/user-agent in a thread-local so
    that model signals (which don't receive the request) can still write a
    complete AuditLog row. This is the standard, minimally-invasive pattern
    for "who did this" logging in Django when you don't want to thread a
    request object through every service function.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, "user", None)
        _thread_locals.ip = self._client_ip(request)
        _thread_locals.user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]
        try:
            response = self.get_response(request)
        finally:
            _thread_locals.user = None
            _thread_locals.ip = None
            _thread_locals.user_agent = ""
        return response

    @staticmethod
    def _client_ip(request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")


def get_current_user():
    user = getattr(_thread_locals, "user", None)
    return user if (user is not None and getattr(user, "is_authenticated", False)) else None


def get_current_ip():
    return getattr(_thread_locals, "ip", None)


def get_current_user_agent():
    # Coalesce None -> "" defensively: user_agent is a NOT NULL CharField,
    # and code running outside any HTTP request (management commands,
    # tests calling services directly) must never pass None through here.
    return getattr(_thread_locals, "user_agent", "") or ""
