import json
import os
import redis
from django.conf import settings
import redis
from rest_framework_simplejwt.authentication import JWTAuthentication
from domain.policies.claim_access_policy import can_access_claim
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
        return _sse_error("Authentication required", status=401)
    job = Job.objects.filter(id=job_id).select_related("claim", "claim__adjuster").first()
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
        try:
            # ── Replay phase: drain all existing stream entries ──────────────
            while True:
                try:
                    entries = r.xread({stream_key: current_id}, block=100, count=100)
                except redis.RedisError as exc:
                    yield f"event: error\ndata: {json.dumps({'message': f'redis read failed: {exc}'})}\n\n"
                    return
                if not entries:
                    break
                _, messages = entries[0]
                for msg_id, fields in messages:
                    current_id = _decode_redis_value(msg_id)
                    replayed_any = True
                    event_type = _decode_redis_value(fields.get(b"type", b"unknown"))
                    data = _decode_redis_value(fields.get(b"data", b"{}"))
                    yield f"id: {current_id}\nevent: {event_type}\ndata: {data}\n\n"
                    if event_type == "status":
                        job_status = json.loads(data).get("status", job_status)

            # ── If nothing replayed, synthesise a current-status event ───────
            if not replayed_any:
                close_old_connections()
                job.refresh_from_db()
                job_status = job.status
                if job_status == "QUEUED":
                    msg = "Job is queued, waiting for a worker"
                else:
                    msg = None
                payload = {"status": job_status}
                if msg:
                    payload["message"] = msg
                yield f"id: {current_id}\nevent: status\ndata: {json.dumps(payload)}\n\n"

            if job_status in TERMINAL_STATUSES or job_status in PAUSE_STATUSES:
                return

            # ── Live-poll phase: wait for new events ─────────────────────────
            elapsed = 0
            max_wait_seconds = 600
            while elapsed < max_wait_seconds:
                try:
                    entries = r.xread({stream_key: current_id}, block=1000, count=50)
                except redis.RedisError as exc:
                    yield f"event: error\ndata: {json.dumps({'message': f'redis read failed: {exc}'})}\n\n"
                    return
                if entries:
                    elapsed = 0
                    _, messages = entries[0]
                    for msg_id, fields in messages:
                        current_id = _decode_redis_value(msg_id)
                        event_type = _decode_redis_value(fields.get(b"type", b"unknown"))
                        data = _decode_redis_value(fields.get(b"data", b"{}"))
                        yield f"id: {current_id}\nevent: {event_type}\ndata: {data}\n\n"
                        if event_type == "status":
                            parsed_status = json.loads(data).get("status")
                            job_status = parsed_status
                            if parsed_status in TERMINAL_STATUSES or parsed_status in PAUSE_STATUSES:
                                return
                else:
                    elapsed += 1
                    if elapsed % 5 == 0:
                        yield ": ping\n\n"
            yield f"event: timeout\ndata: {json.dumps({'message': 'stream timed out waiting for completion'})}\n\n"
        except Exception as exc:
            # Surface unexpected generator crashes as an SSE error event
            # instead of silently dying mid-stream.
            yield f"event: error\ndata: {json.dumps({'message': f'internal stream error: {exc}'})}\n\n"

    return _sse_response(event_stream())
