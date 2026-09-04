from django.test import TestCase
from rest_framework.test import APIClient

from infrastructure.persistence.models import User
from tests.support import make_token


class CreateAdjusterTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.manager = User.objects.create(username="mgr1", role="MANAGER")
        self.adjuster = User.objects.create(username="adj1", role="ADJUSTER")

    def test_manager_can_create_adjuster(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.manager)}")
        response = self.client_api.post("/api/users/adjusters/", {
            "username": "new_adj", "email": "new@example.com", "password": "SecurePass123!",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["role"], "ADJUSTER")
        self.assertNotIn("password", response.data)

    def test_adjuster_forbidden_from_creating_users(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.adjuster)}")
        response = self.client_api.post("/api/users/adjusters/", {
            "username": "should_fail", "password": "SecurePass123!",
        }, format="json")
        self.assertEqual(response.status_code, 403)

    def test_role_field_in_request_is_ignored(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.manager)}")
        response = self.client_api.post("/api/users/adjusters/", {
            "username": "sneaky", "password": "SecurePass123!", "role": "MANAGER",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["role"], "ADJUSTER")  # never MANAGER, regardless of input

    def test_duplicate_username_rejected(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.manager)}")
        response = self.client_api.post("/api/users/adjusters/", {
            "username": "adj1", "password": "SecurePass123!",
        }, format="json")
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_rejected(self):
        response = self.client_api.post("/api/users/adjusters/", {
            "username": "x", "password": "SecurePass123!",
        }, format="json")
        self.assertEqual(response.status_code, 401)


class CurrentUserTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.user = User.objects.create(username="me_test", email="me@example.com", role="ADJUSTER")

    def test_returns_own_info(self):
        self.client_api.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(self.user)}")
        response = self.client_api.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "me_test")
        self.assertEqual(response.data["role"], "ADJUSTER")
        self.assertNotIn("password", response.data)

    def test_unauthenticated_rejected(self):
        response = self.client_api.get("/api/auth/me/")
        self.assertEqual(response.status_code, 401)