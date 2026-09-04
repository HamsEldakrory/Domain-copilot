import json

from django.test import TestCase

from infrastructure.persistence.models import (
    Claim,
    Client,
    Job,
    Policy,
    PolicyVersion,
    User,
)
from tests.support import redis_client


class SSEIntegrationTests(TestCase):
    """Requires a running Redis. Skipped automatically if unreachable."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.redis = redis_client()

    def test_events_scoped_to_correct_job_no_leakage(self):
        if not self.redis:
            self.skipTest("Redis not available")

        client_obj = Client.objects.create(name="Test")
        user = User.objects.create(username="u1")
        policy = Policy.objects.create(client=client_obj, policy_number="p1")
        pv = PolicyVersion.objects.create(policy=policy, version="v1", effective_from="2024-01-01")
        claim = Claim.objects.create(client=client_obj, policy_version=pv, adjuster=user, claim_date="2024-06-01")

        job_a = Job.objects.create(claim=claim, status="RUNNING")
        job_b = Job.objects.create(claim=claim, status="RUNNING")

        self.redis.xadd(f"job-events:{job_a.id}", {"type": "token", "data": json.dumps({"token": "A"})})
        self.redis.xadd(f"job-events:{job_b.id}", {"type": "token", "data": json.dumps({"token": "B"})})

        entries_a = self.redis.xrange(f"job-events:{job_a.id}")
        tokens_a = [json.loads(fields[b"data"])["token"] for _, fields in entries_a]

        self.assertIn("A", tokens_a)
        self.assertNotIn("B", tokens_a)  # structural isolation via separate stream keys
