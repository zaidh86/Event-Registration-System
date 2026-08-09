from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from common.testing import APITestCase
from events.models import Category, EventStatus
from events.tests.helpers import create_attendee, create_organizer


class EventCreateTests(APITestCase):
    url = reverse("events-list")

    def setUp(self):
        super().setUp()
        self.organizer = create_organizer()
        self.category = Category.objects.first()

    def payload(self, **overrides):
        data = {
            "title": "Django Conference",
            "description": "A two-day conference about Django.",
            "category": self.category.id,
            "location": "Cairo",
            "starts_at": (timezone.now() + timedelta(days=30)).isoformat(),
            "capacity": 100,
        }
        data.update(overrides)
        return data

    def test_organizer_creates_draft_event(self):
        self.client.force_authenticate(self.organizer)

        response = self.client.post(self.url, self.payload())

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], EventStatus.DRAFT)
        self.assertEqual(response.data["organizer"], self.organizer.id)
        self.assertEqual(response.data["title"], "Django Conference")

    def test_requires_authentication(self):
        response = self.client.post(self.url, self.payload())

        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")

    def test_attendee_cannot_create_events(self):
        self.client.force_authenticate(create_attendee())

        response = self.client.post(self.url, self.payload())

        self.assertEqual(response.status_code, 403)
        self.assertErrorEnvelope(response, code="permission_denied")

    def test_requires_all_fields(self):
        self.client.force_authenticate(self.organizer)

        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")
        details = response.data["error"]["details"]
        for field in ("title", "description", "category", "location", "starts_at", "capacity"):
            self.assertIn(field, details)

    def test_rejects_non_positive_capacity(self):
        self.client.force_authenticate(self.organizer)

        response = self.client.post(self.url, self.payload(capacity=0))

        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")
        self.assertIn("capacity", response.data["error"]["details"])

    def test_rejects_unknown_category(self):
        self.client.force_authenticate(self.organizer)

        response = self.client.post(self.url, self.payload(category=999999))

        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")
        self.assertIn("category", response.data["error"]["details"])

    def test_client_cannot_set_status(self):
        self.client.force_authenticate(self.organizer)

        response = self.client.post(self.url, self.payload(status=EventStatus.PUBLISHED))

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], EventStatus.DRAFT)
