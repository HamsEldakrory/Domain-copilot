import os

import ollama
import redis
from rest_framework_simplejwt.tokens import RefreshToken


def make_token(user):
    return str(RefreshToken.for_user(user).access_token)


def redis_client():
    url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    try:
        client = redis.Redis.from_url(url)
        client.ping()
        return client
    except redis.ConnectionError:
        return None


def ollama_available():
    try:
        ollama.Client(host=os.getenv("OLLAMA_HOST")).list()
        return True
    except Exception:
        return False
