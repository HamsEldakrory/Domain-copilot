from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient


class OpenAPISchemaTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_schema_endpoint_returns_valid_openapi(self):
        client = APIClient()
        response = client.get("/api/schema/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("openapi", content)
        self.assertIn("/api/adjudicate/", content)
