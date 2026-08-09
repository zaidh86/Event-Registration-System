from django.urls import reverse

from common.testing import APITestCase
from users import services
from users.models import UserRole


class MeViewTests(APITestCase):
    url = reverse("users-me")

    def setUp(self):
        super().setUp()
        self.user = services.create_user(
            email="attendee@example.com",
            password="correct-horse-battery",
            first_name="Ada",
            last_name="Lovelace",
            role=UserRole.ATTENDEE,
        )
        self.client.force_authenticate(self.user)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")

    def test_get_returns_current_user(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data),
            {"id", "email", "first_name", "last_name", "role", "date_joined"},
        )
        self.assertEqual(response.data["email"], "attendee@example.com")
        self.assertEqual(response.data["role"], UserRole.ATTENDEE)

    def test_patch_updates_names(self):
        response = self.client.patch(self.url, {"first_name": "Grace", "last_name": "Hopper"})

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Grace")
        self.assertEqual(self.user.last_name, "Hopper")

    def test_patch_ignores_email_and_role(self):
        response = self.client.patch(
            self.url,
            {"email": "changed@example.com", "role": UserRole.ORGANIZER},
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "attendee@example.com")
        self.assertEqual(self.user.role, UserRole.ATTENDEE)

    def test_put_is_not_allowed(self):
        response = self.client.put(self.url, {"first_name": "Grace", "last_name": "Hopper"})

        self.assertEqual(response.status_code, 405)
        self.assertErrorEnvelope(response, code="method_not_allowed")
