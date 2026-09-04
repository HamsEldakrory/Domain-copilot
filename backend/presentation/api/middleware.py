import threading
import uuid

_local = threading.local()

def get_correlation_id():
    return getattr(_local, "correlation_id", None)

class CorrelationIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.correlation_id = correlation_id
        response = self.get_response(request)
        response["X-Correlation-ID"] = correlation_id
        return response


class SecurityHeadersMiddleware:
    """Adds security headers to every response that are not handled by Django's
    SecurityMiddleware (which only sets them on HTTPS in production)."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["X-Frame-Options"] = "DENY"
        response["X-Content-Type-Options"] = "nosniff"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Instruct browsers to use CSP instead of legacy XSS filter
        response["X-XSS-Protection"] = "0"
        return response