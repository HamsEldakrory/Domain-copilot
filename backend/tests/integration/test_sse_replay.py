import json

from django.test import TestCase
from django.test.client import RequestFactory

from infrastructure.persistence.models import (
    Claim,
    Client,
    Job,
    Policy,
    PolicyVersion,
    User,
)
from presentation.api.sse import job_progress_stream
from tests.support import make_token, redis_client


class SSEReplayTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.redis = redis_client()

    def setUp(self):
        if not self.redis:
            self.skipTest("Redis not available")
        self.org = Client.objects.create(name="SSE Test Org")
        self.user = User.objects.create(username="sse_user", role="ADJUSTER")
        policy = Policy.objects.create(client=self.org, policy_number="sse-test")
        self.pv = PolicyVersion.objects.create(policy=policy, version="v1", effective_from="2024-01-01")
        self.claim = Claim.objects.create(client=self.org, policy_version=self.pv, adjuster=self.user, claim_date="2024-06-01")
        self.factory = RequestFactory()
        self.token = make_token(self.user)

    def _make_request(self, job_id, last_event_id=None):
        headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}
        if last_event_id:
            headers["HTTP_LAST_EVENT_ID"] = last_event_id
        return self.factory.get(f"/api/jobs/{job_id}/stream/", **headers)

    def test_late_connect_replays_history_even_when_job_already_completed(self):
        job = Job.objects.create(claim=self.claim, status="COMPLETED")
        stream_key = f"job-events:{job.id}"
        self.redis.xadd(stream_key, {"type": "agent_started", "data": json.dumps({"agent": "coverage_matcher"})})
        self.redis.xadd(stream_key, {"type": "token", "data": json.dumps({"token": "hello"})})
        self.redis.xadd(stream_key, {"type": "status", "data": json.dumps({"status": "COMPLETED"})})

        request = self._make_request(job.id)
        response = job_progress_stream(request, str(job.id))
        body = b"".join(response.streaming_content).decode()

        self.assertIn("agent_started", body)
        self.assertIn("hello", body)
        self.assertIn("COMPLETED", body)

    def test_last_event_id_resumes_from_that_point_not_from_scratch(self):
        job = Job.objects.create(claim=self.claim, status="COMPLETED")
        stream_key = f"job-events:{job.id}"
        id1 = self.redis.xadd(stream_key, {"type": "token", "data": json.dumps({"token": "first"})}).decode()
        self.redis.xadd(stream_key, {"type": "token", "data": json.dumps({"token": "second"})})
        self.redis.xadd(stream_key, {"type": "status", "data": json.dumps({"status": "COMPLETED"})})

        request = self._make_request(job.id, last_event_id=id1)
        response = job_progress_stream(request, str(job.id))
        body = b"".join(response.streaming_content).decode()

        self.assertNotIn("first", body)  # already seen before this id, must not repeat
        self.assertIn("second", body)

    def test_no_leakage_between_jobs(self):
        job_a = Job.objects.create(claim=self.claim, status="COMPLETED")
        job_b = Job.objects.create(claim=self.claim, status="COMPLETED")
        self.redis.xadd(f"job-events:{job_a.id}", {"type": "token", "data": json.dumps({"token": "A-only"})})
        self.redis.xadd(f"job-events:{job_b.id}", {"type": "token", "data": json.dumps({"token": "B-only"})})

        request = self._make_request(job_a.id)
        response = job_progress_stream(request, str(job_a.id))
        body = b"".join(response.streaming_content).decode()

        self.assertIn("A-only", body)
        self.assertNotIn("B-only", body)
