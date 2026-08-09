from django.urls import reverse

from common.testing import APITestCase
from users import services
from users.models import UserRole


class LoginTests(APITestCase):
    url = reverse("auth-login")

    def setUp(self):
        super().setUp()
        services.create_user(
            email="organizer@example.com",
            password="correct-horse-battery",
            first_name="Grace",
            last_name="Hopper",
            role=UserRole.ORGANIZER,
        )

    def test_login_success(self):
        response = self.client.post(
            self.url,
            {"email": "organizer@example.com", "password": "correct-horse-battery"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_is_case_insensitive_on_email(self):
        response = self.client.post(
            self.url,
            {"email": "ORGANIZER@example.com", "password": "correct-horse-battery"},
        )

        self.assertEqual(response.status_code, 200)

    def test_login_rejects_wrong_password(self):
        response = self.client.post(
            self.url,
            {"email": "organizer@example.com", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="no_active_account")

    def test_login_rejects_unknown_email(self):
        response = self.client.post(
            self.url,
            {"email": "nobody@example.com", "password": "correct-horse-battery"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="no_active_account")
