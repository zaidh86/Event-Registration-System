from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from common.testing import APITestCase
from events.models import EventStatus
from events.tests.helpers import create_event, create_organizer


class EventPublishTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.organizer = create_organizer()

    def url(self, event):
        return reverse("events-publish", args=[event.id])

    def test_publishes_draft_event(self):
        event = create_event(self.organizer)
        self.client.force_authenticate(self.organizer)

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], EventStatus.PUBLISHED)
        event.refresh_from_db()
        self.assertEqual(event.status, EventStatus.PUBLISHED)

    def test_requires_future_start(self):
        event = create_event(self.organizer, starts_at=timezone.now() - timedelta(hours=1))
        self.client.force_authenticate(self.organizer)

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="event_start_in_past")

    def test_rejects_already_published_event(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED)
        self.client.force_authenticate(self.organizer)

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="invalid_status_transition")

    def test_rejects_cancelled_event(self):
        event = create_event(self.organizer, status=EventStatus.CANCELLED)
        self.client.force_authenticate(self.organizer)

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="invalid_status_transition")

    def test_requires_authentication(self):
        event = create_event(self.organizer)

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")

    def test_non_owner_gets_404_for_draft(self):
        event = create_event(self.organizer)
        self.client.force_authenticate(create_organizer("other@example.com"))

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 404)
        self.assertErrorEnvelope(response, code="not_found")


class EventCancelTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.organizer = create_organizer()

    def url(self, event):
        return reverse("events-cancel", args=[event.id])

    def test_cancels_published_event(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED)
        self.client.force_authenticate(self.organizer)

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], EventStatus.CANCELLED)
        event.refresh_from_db()
        self.assertEqual(event.status, EventStatus.CANCELLED)

    def test_rejects_draft_event(self):
        event = create_event(self.organizer)
        self.client.force_authenticate(self.organizer)

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="invalid_status_transition")

    def test_cancelled_is_terminal(self):
        event = create_event(self.organizer, status=EventStatus.CANCELLED)
        self.client.force_authenticate(self.organizer)

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="invalid_status_transition")

    def test_non_owner_cannot_cancel(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED)
        self.client.force_authenticate(create_organizer("other@example.com"))

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 403)
        self.assertErrorEnvelope(response, code="permission_denied")

    def test_requires_authentication(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED)

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")
