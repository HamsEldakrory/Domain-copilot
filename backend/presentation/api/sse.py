import json
from django.http import StreamingHttpResponse
from django.conf import settings
import redis
from infrastructure.persistence.models import Job
TERMINAL_STATUSES = {"COMPLETED", "FAILED", "CANCELLED"}
PAUSE_STATUSES = {"WAITING_APPROVAL"}  # closes this connection but job isn't finished

def job_progress_stream(request, job_id):
    r = redis.Redis.from_url(getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0"))
    stream_key = f"job-events:{job_id}"
    def event_stream():
        job = Job.objects.filter(id=job_id).first()
        if not job:
            yield f"event: error\ndata: {json.dumps({'error': 'job not found'})}\n\n"
            return
        yield f"event: status\ndata: {json.dumps({'status': job.status})}\n\n"
        if job.status in TERMINAL_STATUSES or job.status in PAUSE_STATUSES:
            return
        last_id = "0"
        max_wait_seconds = 180
        elapsed = 0
        while elapsed < max_wait_seconds:
            entries = r.xread({stream_key: last_id}, block=1000, count=50)
            if entries:
                _, messages = entries[0]
                for msg_id, fields in messages:
                    last_id = msg_id
                    event_type = fields.get(b"type", b"message").decode()
                    data = fields.get(b"data", b"{}").decode()
                    yield f"event: {event_type}\ndata: {data}\n\n"

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