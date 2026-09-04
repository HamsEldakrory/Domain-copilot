from django.test import TestCase
from rest_framework.test import APIClient

from infrastructure.persistence.models import (
    AuditLog,
    Claim,
    Client,
    Decision,
    Job,
    Policy,
    PolicyVersion,
    User,
)
from tests.support import make_token


class ApprovalDecisionTests(TestCase):
    def setUp(self):
        self.api = APIClient()
        self.org = Client.objects.create(name="Test Org")
        self.adjuster = User.objects.create(username="adjuster1", role="ADJUSTER")
        self.policy = Policy.objects.create(client=self.org, policy_number="P100")
        self.pv = PolicyVersion.objects.create(policy=self.policy, version="v1", effective_from="2024-01-01")
        self.claim = Claim.objects.create(client=self.org, policy_version=self.pv, adjuster=self.adjuster, claim_date="2024-06-01")
        self.job = Job.objects.create(claim=self.claim, status="WAITING_APPROVAL")
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.adjuster)}")

    def test_approve_decision_with_decimal_payout(self):
        payload = {
            "decision": "edit",
            "outcome": "approved",
            "rationale": "Updated payout after review",
            "comment": "Adjusted payout from original recommendation",
            "final_payout": 1500.50,
            "original_recommendation": {
                "outcome": "approved",
                "payout": 1000.00,
                "rationale": "Original recommendation rationale"
            }
        }
        response = self.api.post(f"/api/jobs/{self.job.id}/approve/", payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("status"), "edited_and_approved")

        self.job.refresh_from_db()
        self.assertEqual(self.job.status, "COMPLETED")

        self.claim.refresh_from_db()
        self.assertEqual(self.claim.status, "decided")
        self.assertEqual(float(self.claim.final_payout), 1500.50)

        decision = Decision.objects.get(job=self.job)
        self.assertEqual(decision.outcome, "approved")
        self.assertEqual(decision.rationale, "Updated payout after review")
        self.assertEqual(float(decision.final_payout), 1500.50)

        audit_logs = AuditLog.objects.filter(job=self.job)
        self.assertTrue(audit_logs.exists())
