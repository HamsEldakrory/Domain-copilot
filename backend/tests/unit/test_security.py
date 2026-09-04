from django.core.cache import cache
from django.test import Client, TestCase


class SecurityHeadersTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_security_headers_present(self):
        response = self.client.get("/api/docs/")
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["Referrer-Policy"], "strict-origin-when-cross-origin")
        self.assertEqual(response["X-XSS-Protection"], "0")


class RateLimitTest(TestCase):
    def setUp(self):
        self.client = Client()

    def tearDown(self):
        cache.clear()

    def test_rate_limit_applied_anon(self):
        for _ in range(20):
            self.client.get("/api/docs/")
        response = self.client.get("/api/docs/")
        self.assertEqual(response.status_code, 429)


class PIIAndDataIsolationTest(TestCase):
    def test_pii_isolation(self):
        # Covered by integration/test_indirect_injection.py and integration/test_auth_and_roles.py.
        pass
