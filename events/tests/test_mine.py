from django.urls import reverse

from common.testing import APITestCase
from events.models import EventStatus
from events.tests.helpers import create_attendee, create_event, create_organizer


class MyEventsTests(APITestCase):
    url = reverse("events-mine")

    def setUp(self):
        super().setUp()
        self.organizer = create_organizer()

    def test_lists_own_events_of_every_status(self):
        draft = create_event(self.organizer, title="Draft")
        published = create_event(
            self.organizer, title="Published", status=EventStatus.PUBLISHED
        )
        cancelled = create_event(
            self.organizer, title="Cancelled", status=EventStatus.CANCELLED
        )
        create_event(create_organizer("other@example.com"), title="Someone else's")
        self.client.force_authenticate(self.organizer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        ids = {item["id"] for item in response.data["results"]}
        self.assertEqual(ids, {draft.id, published.id, cancelled.id})

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")

    def test_attendee_is_forbidden(self):
        self.client.force_authenticate(create_attendee())

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertErrorEnvelope(response, code="permission_denied")
