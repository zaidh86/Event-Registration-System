from django.urls import reverse

from common.testing import APITestCase
from users.models import User, UserRole


def payload(**overrides):
    data = {
        "email": "attendee@example.com",
        "password": "correct-horse-battery",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "role": UserRole.ATTENDEE,
    }
    data.update(overrides)
    return data


class RegisterTests(APITestCase):
    url = reverse("auth-register")

    def test_register_success(self):
        response = self.client.post(self.url, payload())

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["email"], "attendee@example.com")
        self.assertEqual(response.data["first_name"], "Ada")
        self.assertEqual(response.data["last_name"], "Lovelace")
        self.assertEqual(response.data["role"], UserRole.ATTENDEE)
        self.assertNotIn("password", response.data)
        user = User.objects.get(email="attendee@example.com")
        self.assertTrue(user.check_password("correct-horse-battery"))

    def test_register_stores_email_lowercased(self):
        response = self.client.post(self.url, payload(email="Mixed.Case@Example.COM"))

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["email"], "mixed.case@example.com")

    def test_register_duplicate_email_is_case_insensitive(self):
        self.client.post(self.url, payload())
        response = self.client.post(self.url, payload(email="ATTENDEE@example.com"))

        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")
        self.assertIn("email", response.data["error"]["details"])

    def test_register_rejects_weak_password(self):
        response = self.client.post(self.url, payload(password="short"))

        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")
        self.assertIn("password", response.data["error"]["details"])

    def test_register_rejects_invalid_role(self):
        response = self.client.post(self.url, payload(role="ADMIN"))

        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")
        self.assertIn("role", response.data["error"]["details"])

    def test_register_requires_all_fields(self):
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")
        details = response.data["error"]["details"]
        for field in ("email", "password", "first_name", "last_name", "role"):
            self.assertIn(field, details)
