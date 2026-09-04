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

    def test_unauthenticated_stream_forbidden(self):
        job = Job.objects.create(claim=self.claim, status="RUNNING")
        request = self.factory.get(f"/api/jobs/{job.id}/stream/")
        response = job_progress_stream(request, str(job.id))
        self.assertEqual(response.status_code, 401)
        body = b"".join(response.streaming_content).decode()
        self.assertIn("Authentication required", body)

    def test_other_adjuster_stream_forbidden(self):
        other = User.objects.create(username="other_adj", role="ADJUSTER")
        job = Job.objects.create(claim=self.claim, status="RUNNING")
        token = make_token(other)
        request = self.factory.get(
            f"/api/jobs/{job.id}/stream/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        response = job_progress_stream(request, str(job.id))
        self.assertEqual(response.status_code, 403)
        body = b"".join(response.streaming_content).decode()
        self.assertIn("do not have access", body)

    def test_manager_can_stream_any_claim_job(self):
        manager = User.objects.create(username="mgr_stream", role="MANAGER")
        job = Job.objects.create(claim=self.claim, status="COMPLETED")
        stream_key = f"job-events:{job.id}"
        self.redis.xadd(stream_key, {"type": "status", "data": json.dumps({"status": "COMPLETED"})})

        request = self.factory.get(
            f"/api/jobs/{job.id}/stream/",
            HTTP_AUTHORIZATION=f"Bearer {make_token(manager)}",
        )
        response = job_progress_stream(request, str(job.id))
        self.assertEqual(response.status_code, 200)
        body = b"".join(response.streaming_content).decode()
        self.assertIn("COMPLETED", body)
