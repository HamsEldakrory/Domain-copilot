from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from infrastructure.persistence.models import User
from tests.support import make_token


class PolicyUploadTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.manager = User.objects.create(username="mgr_upload", role="MANAGER")
        self.adjuster = User.objects.create(username="adj_upload", role="ADJUSTER")

    @patch("infrastructure.tasks.ingest_document_task.delay")
    def test_manager_can_upload(self, mock_delay):
        self.client_api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.manager)}")
        f = SimpleUploadedFile("test_policy.pdf", b"%PDF-1.4 fake content", content_type="application/pdf")
        response = self.client_api.post("/api/policies/upload/", {
            "file": f, "policy_number": "test_new", "version": "2026-01",
            "effective_from": "2026-01-01", "policy_limit": "50000", "deductible": "1000",
        }, format="multipart")
        self.assertEqual(response.status_code, 202)
        mock_delay.assert_called_once()

    def test_adjuster_forbidden(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.adjuster)}")
        f = SimpleUploadedFile("test.pdf", b"content", content_type="application/pdf")
        response = self.client_api.post("/api/policies/upload/", {
            "file": f, "policy_number": "x", "version": "v1",
            "effective_from": "2026-01-01", "policy_limit": "1000", "deductible": "100",
        }, format="multipart")
        self.assertEqual(response.status_code, 403)

    def test_non_pdf_docx_rejected(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.manager)}")
        f = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")
        response = self.client_api.post("/api/policies/upload/", {
            "file": f, "policy_number": "x", "version": "v1",
            "effective_from": "2026-01-01", "policy_limit": "1000", "deductible": "100",
        }, format="multipart")
        self.assertEqual(response.status_code, 400)