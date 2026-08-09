from django.urls import reverse

from common.testing import APITestCase
from users import services
from users.models import UserRole


class TokenTests(APITestCase):
    login_url = reverse("auth-login")
    refresh_url = reverse("auth-refresh")
    logout_url = reverse("auth-logout")

    def setUp(self):
        super().setUp()
        services.create_user(
            email="attendee@example.com",
            password="correct-horse-battery",
            first_name="Ada",
            last_name="Lovelace",
            role=UserRole.ATTENDEE,
        )

    def login(self):
        response = self.client.post(
            self.login_url,
            {"email": "attendee@example.com", "password": "correct-horse-battery"},
        )
        self.assertEqual(response.status_code, 200)
        return response.data

    def test_access_token_authenticates_requests(self):
        tokens = self.login()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        response = self.client.get(reverse("users-me"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "attendee@example.com")

    def test_refresh_rotates_and_blacklists_previous_token(self):
        tokens = self.login()

        rotated = self.client.post(self.refresh_url, {"refresh": tokens["refresh"]})
        self.assertEqual(rotated.status_code, 200)
        self.assertIn("access", rotated.data)
        self.assertIn("refresh", rotated.data)
        self.assertNotEqual(rotated.data["refresh"], tokens["refresh"])

        replayed = self.client.post(self.refresh_url, {"refresh": tokens["refresh"]})
        self.assertEqual(replayed.status_code, 401)
        self.assertErrorEnvelope(replayed, code="token_not_valid")

    def test_logout_blacklists_refresh_token(self):
        tokens = self.login()

        response = self.client.post(self.logout_url, {"refresh": tokens["refresh"]})
        self.assertEqual(response.status_code, 200)

        reused = self.client.post(self.refresh_url, {"refresh": tokens["refresh"]})
        self.assertEqual(reused.status_code, 401)
        self.assertErrorEnvelope(reused, code="token_not_valid")

    def test_protected_endpoint_rejects_missing_token(self):
        response = self.client.get(reverse("users-me"))

        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")
