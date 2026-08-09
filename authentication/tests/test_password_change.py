from django.urls import reverse

from common.testing import APITestCase
from users import services
from users.models import UserRole


class PasswordChangeTests(APITestCase):
    url = reverse("auth-password-change")
    login_url = reverse("auth-login")
    refresh_url = reverse("auth-refresh")

    def setUp(self):
        super().setUp()
        self.user = services.create_user(
            email="attendee@example.com",
            password="correct-horse-battery",
            first_name="Ada",
            last_name="Lovelace",
            role=UserRole.ATTENDEE,
        )

    def login(self, password="correct-horse-battery"):
        response = self.client.post(
            self.login_url,
            {"email": "attendee@example.com", "password": password},
        )
        return response

    def authenticate(self):
        tokens = self.login().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        return tokens

    def test_requires_authentication(self):
        response = self.client.post(
            self.url,
            {"current_password": "correct-horse-battery", "new_password": "brand-new-passphrase"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")

    def test_rejects_wrong_current_password(self):
        self.authenticate()

        response = self.client.post(
            self.url,
            {"current_password": "wrong-password", "new_password": "brand-new-passphrase"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")
        self.assertIn("current_password", response.data["error"]["details"])

    def test_rejects_weak_new_password(self):
        self.authenticate()

        response = self.client.post(
            self.url,
            {"current_password": "correct-horse-battery", "new_password": "short"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")
        self.assertIn("new_password", response.data["error"]["details"])

    def test_change_password_success(self):
        self.authenticate()

        response = self.client.post(
            self.url,
            {"current_password": "correct-horse-battery", "new_password": "brand-new-passphrase"},
        )
        self.assertEqual(response.status_code, 204)

        self.client.credentials()
        self.assertEqual(self.login(password="correct-horse-battery").status_code, 401)
        self.assertEqual(self.login(password="brand-new-passphrase").status_code, 200)

    def test_change_password_revokes_outstanding_refresh_tokens(self):
        tokens = self.authenticate()

        response = self.client.post(
            self.url,
            {"current_password": "correct-horse-battery", "new_password": "brand-new-passphrase"},
        )
        self.assertEqual(response.status_code, 204)

        reused = self.client.post(self.refresh_url, {"refresh": tokens["refresh"]})
        self.assertEqual(reused.status_code, 401)
        self.assertErrorEnvelope(reused, code="token_not_valid")
