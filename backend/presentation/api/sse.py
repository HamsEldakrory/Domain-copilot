import json
from django.http import StreamingHttpResponse, HttpResponseForbidden
from django.conf import settings
import redis
from rest_framework_simplejwt.authentication import JWTAuthentication
from infrastructure.persistence.models import Job
from domain.policies.claim_access_policy import can_access_claim

TERMINAL_STATUSES = {"COMPLETED", "FAILED", "CANCELLED"}
PAUSE_STATUSES = {"WAITING_APPROVAL"}
def _authenticate_sse(request):
    """
    EventSource cannot send headers, so the JWT is passed as ?access=<token>.
    Inject it as a fake Authorization header if the real one is absent.
    """
    if not request.headers.get("Authorization"):
        token = request.GET.get("access", "")
        if token:
            # Mutate the META dict — DRF reads HTTP_AUTHORIZATION from it
            request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    try:
        result = JWTAuthentication().authenticate(request)
        if result is None:
            return None, None
        return result  # (user, validated_token)
    except Exception:
        return None, None


def job_progress_stream(request, job_id):
    user, _ = _authenticate_sse(request)
    if not user:
        return HttpResponseForbidden("Authentication required")

    job = Job.objects.filter(id=job_id).select_related("claim").first()
    if not job:
        return HttpResponseForbidden("Job not found")
    if not can_access_claim(getattr(user, "role", ""), str(user.id), str(job.claim.adjuster_id)):
        return HttpResponseForbidden("You do not have access to this job")

    r = redis.Redis.from_url(getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0"))
    stream_key = f"job-events:{job_id}"
    start_id = request.headers.get("Last-Event-ID") or request.GET.get("last_event_id") or "0"

    def event_stream():
        current_id = start_id
        replayed_any = False
        while True:
            entries = r.xread({stream_key: current_id}, block=100, count=100)
            if not entries:
                break
            _, messages = entries[0]
            for msg_id, fields in messages:
                current_id = msg_id.decode()
                replayed_any = True
                event_type = fields[b"type"].decode()
                data = fields[b"data"].decode()
                yield f"id: {current_id}\nevent: {event_type}\ndata: {data}\n\n"

        job.refresh_from_db()
        if not replayed_any:
            yield f"id: {current_id}\nevent: status\ndata: {json.dumps({'status': job.status})}\n\n"
        if job.status in TERMINAL_STATUSES or job.status in PAUSE_STATUSES:
            return
        elapsed = 0
        max_wait_seconds = 180
        while elapsed < max_wait_seconds:
            entries = r.xread({stream_key: current_id}, block=1000, count=50)
            if entries:
                _, messages = entries[0]
                for msg_id, fields in messages:
                    current_id = msg_id.decode()
                    event_type = fields[b"type"].decode()
                    data = fields[b"data"].decode()
                    yield f"id: {current_id}\nevent: {event_type}\ndata: {data}\n\n"
                    if event_type == "status":
                        parsed_status = json.loads(data).get("status")
                        if parsed_status in TERMINAL_STATUSES or parsed_status in PAUSE_STATUSES:
                            return
            else:
                elapsed += 1
        yield f"event: timeout\ndata: {json.dumps({'message': 'stream timed out waiting for completion'})}\n\n"
    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response