from django.urls import reverse

from common.testing import APITestCase
from events.models import EventStatus
from events.tests.helpers import create_attendee, create_event, create_organizer


class EventDetailTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.organizer = create_organizer()

    def url(self, event):
        return reverse("events-detail", args=[event.id])

    def test_published_event_is_publicly_visible(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED)

        response = self.client.get(self.url(event))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], event.id)
        self.assertEqual(
            set(response.data),
            {
                "id",
                "organizer",
                "title",
                "description",
                "category",
                "location",
                "starts_at",
                "capacity",
                "status",
                "created_at",
                "updated_at",
            },
        )

    def test_cancelled_event_is_publicly_visible(self):
        event = create_event(self.organizer, status=EventStatus.CANCELLED)

        response = self.client.get(self.url(event))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], EventStatus.CANCELLED)

    def test_draft_is_visible_to_its_organizer(self):
        event = create_event(self.organizer)
        self.client.force_authenticate(self.organizer)

        response = self.client.get(self.url(event))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], EventStatus.DRAFT)

    def test_draft_is_hidden_from_other_users(self):
        event = create_event(self.organizer)

        for user in (create_organizer("other@example.com"), create_attendee()):
            self.client.force_authenticate(user)
            response = self.client.get(self.url(event))
            self.assertEqual(response.status_code, 404)
            self.assertErrorEnvelope(response, code="not_found")

    def test_draft_is_hidden_from_anonymous_users(self):
        event = create_event(self.organizer)

        response = self.client.get(self.url(event))

        self.assertEqual(response.status_code, 404)
        self.assertErrorEnvelope(response, code="not_found")

    def test_missing_event_returns_404(self):
        response = self.client.get(reverse("events-detail", args=[999999]))

        self.assertEqual(response.status_code, 404)
        self.assertErrorEnvelope(response, code="not_found")
