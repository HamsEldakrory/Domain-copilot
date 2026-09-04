import json

import redis
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from domain.ports.job_event_publisher import JobEventPublisher

STREAM_TTL_SECONDS = 3600  # cleanup - events for a job don't need to outlive an hour


def _redis_url():
    url = getattr(settings, "CELERY_BROKER_URL", None)
    return url


class RedisJobEventPublisher(JobEventPublisher):
    def __init__(self):
        self._redis = redis.Redis.from_url(_redis_url())

    def publish(self, job_id: str, event_type: str, data: dict) -> None:
        stream_key = f"job-events:{job_id}"
        self._redis.xadd(stream_key, {"type": event_type, "data": json.dumps(data, cls=DjangoJSONEncoder)})
        self._redis.expire(stream_key, STREAM_TTL_SECONDS)