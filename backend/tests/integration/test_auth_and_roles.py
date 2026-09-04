from django.test import TestCase
from rest_framework.test import APIClient

from infrastructure.persistence.models import Claim, Client, Policy, PolicyVersion, User
from tests.support import make_token


class AuthAndRoleTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.org = Client.objects.create(name="Test Org")
        self.adjuster_a = User.objects.create(username="adj_a", role="ADJUSTER")
        self.adjuster_b = User.objects.create(username="adj_b", role="ADJUSTER")
        self.manager = User.objects.create(username="mgr", role="MANAGER")

        policy = Policy.objects.create(client=self.org, policy_number="test")
        self.pv = PolicyVersion.objects.create(policy=policy, version="v1", effective_from="2024-01-01", policy_limit=10000, deductible=500)
        self.claim = Claim.objects.create(client=self.org, policy_version=self.pv, adjuster=self.adjuster_a, claim_date="2024-06-01")

    def test_unauthenticated_request_rejected(self):
        response = self.client_api.post("/api/adjudicate/", {"claim_id": str(self.claim.id), "claimed_amount": 1000}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_owning_adjuster_can_access(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.adjuster_a)}")
        response = self.client_api.post("/api/adjudicate/", {"claim_id": str(self.claim.id), "claimed_amount": 1000}, format="json")
        self.assertIn(response.status_code, [200, 202])

    def test_other_adjuster_forbidden(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.adjuster_b)}")
        response = self.client_api.post("/api/adjudicate/", {"claim_id": str(self.claim.id), "claimed_amount": 1000}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_manager_can_access_any_claim(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.manager)}")
        response = self.client_api.post("/api/adjudicate/", {"claim_id": str(self.claim.id), "claimed_amount": 1000}, format="json")
        self.assertIn(response.status_code, [200, 202])