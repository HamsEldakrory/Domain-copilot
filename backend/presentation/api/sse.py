import json
import os
import redis
from django.conf import settings
from django.db import close_old_connections
from django.http import StreamingHttpResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from domain.policies.claim_access_policy import can_access_claim
from infrastructure.persistence.models import Job

TERMINAL_STATUSES = {"COMPLETED", "FAILED", "CANCELLED"}
PAUSE_STATUSES = {"WAITING_APPROVAL"}


def _redis_url():
    return (
        getattr(settings, "CELERY_BROKER_URL", None)
        or os.getenv("CELERY_BROKER_URL")
    )

def _decode_redis_value(value):
    return value.decode() if isinstance(value, bytes) else value

def _sse_response(body, status=200):
    response = StreamingHttpResponse(body, content_type="text/event-stream", status=status)
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response

def _sse_error(message, status=200):
    payload = json.dumps({"message": message})
    def body():
        yield f"event: error\ndata: {payload}\n\n"
    return _sse_response(body(), status=status)

def _authenticate_sse(request):
    if not request.headers.get("Authorization"):
        token = request.GET.get("access", "")
        if token:
            request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    try:
        result = JWTAuthentication().authenticate(request)
        if result is None:
            return None, None
        return result
    except Exception:
        return None, None
    
def job_progress_stream(request, job_id):
    user, _ = _authenticate_sse(request)
    if not user:
        return _sse_error("Authentication required", status=401)
    job = Job.objects.filter(id=job_id).select_related("claim").first()
    if not job:
        return _sse_error("Job not found", status=404)
    if not can_access_claim(getattr(user, "role", ""), str(user.id), str(job.claim.adjuster_id)):
        return _sse_error("You do not have access to this job", status=403)
    try:
        r = redis.Redis.from_url(_redis_url())
        r.ping()
    except redis.RedisError:
        return _sse_error("Stream backend unavailable", status=503)
    stream_key = f"job-events:{job_id}"
    start_id = request.headers.get("Last-Event-ID") or request.GET.get("last_event_id") or "0"
    job_status = job.status
    
    def event_stream():
        nonlocal job_status
        current_id = start_id
        replayed_any = False
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
                event_type = _decode_redis_value(fields[b"type"])
                data = _decode_redis_value(fields[b"data"])
                yield f"id: {current_id}\nevent: {event_type}\ndata: {data}\n\n"
                if event_type == "status":
                    job_status = json.loads(data).get("status", job_status)

        if not replayed_any:
            close_old_connections()
            job.refresh_from_db()
            job_status = job.status
            yield f"id: {current_id}\nevent: status\ndata: {json.dumps({'status': job_status})}\n\n"

        if job_status in TERMINAL_STATUSES or job_status in PAUSE_STATUSES:
            return

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
                    event_type = _decode_redis_value(fields[b"type"])
                    data = _decode_redis_value(fields[b"data"])
                    yield f"id: {current_id}\nevent: {event_type}\ndata: {data}\n\n"
                    if event_type == "status":
                        parsed_status = json.loads(data).get("status")
                        job_status = parsed_status
                        if parsed_status in TERMINAL_STATUSES or parsed_status in PAUSE_STATUSES:
                            return
            else:
                elapsed += 1
                if elapsed % 15 == 0:
                    yield ": ping\n\n"
        yield f"event: timeout\ndata: {json.dumps({'message': 'stream timed out waiting for completion'})}\n\n"

    return _sse_response(event_stream())
