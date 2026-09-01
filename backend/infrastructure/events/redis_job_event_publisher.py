import json
import redis
from django.conf import settings
from domain.ports.job_event_publisher import JobEventPublisher
STREAM_TTL_SECONDS = 3600  # cleanup - events for a job don't need to outlive an hour

class RedisJobEventPublisher(JobEventPublisher):
    def __init__(self):
        self._redis = redis.Redis.from_url(getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0"))

    def publish(self, job_id: str, event_type: str, data: dict) -> None:
        stream_key = f"job-events:{job_id}"
        self._redis.xadd(stream_key, {"type": event_type, "data": json.dumps(data)})
        self._redis.expire(stream_key, STREAM_TTL_SECONDS)