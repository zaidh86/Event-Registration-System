from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from common.testing import APITestCase
from events.models import EventStatus
from events.tests.helpers import create_attendee, create_event, create_organizer
from registrations.models import RegistrationStatus
from registrations.tests.helpers import create_registration


class EventUpdateTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.organizer = create_organizer()

    def url(self, event):
        return reverse("events-detail", args=[event.id])

    def test_owner_updates_draft(self):
        event = create_event(self.organizer)
        self.client.force_authenticate(self.organizer)

        response = self.client.patch(self.url(event), {"title": "PyCon", "capacity": 50})

        self.assertEqual(response.status_code, 200)
        event.refresh_from_db()
        self.assertEqual(event.title, "PyCon")
        self.assertEqual(event.capacity, 50)

    def test_requires_authentication(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED)

        response = self.client.patch(self.url(event), {"title": "PyCon"})

        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")

    def test_non_owner_cannot_update_visible_event(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED)
        self.client.force_authenticate(create_organizer("other@example.com"))

        response = self.client.patch(self.url(event), {"title": "PyCon"})

        self.assertEqual(response.status_code, 403)
        self.assertErrorEnvelope(response, code="permission_denied")

    def test_non_owner_gets_404_for_draft(self):
        event = create_event(self.organizer)
        self.client.force_authenticate(create_organizer("other@example.com"))

        response = self.client.patch(self.url(event), {"title": "PyCon"})

        self.assertEqual(response.status_code, 404)
        self.assertErrorEnvelope(response, code="not_found")

    def test_cancelled_event_is_not_editable(self):
        event = create_event(self.organizer, status=EventStatus.CANCELLED)
        self.client.force_authenticate(self.organizer)

        response = self.client.patch(self.url(event), {"title": "PyCon"})

        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="event_not_editable")

    def test_past_published_event_is_not_editable(self):
        event = create_event(
            self.organizer,
            status=EventStatus.PUBLISHED,
            starts_at=timezone.now() - timedelta(hours=1),
        )
        self.client.force_authenticate(self.organizer)

        response = self.client.patch(self.url(event), {"title": "PyCon"})

        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="event_not_editable")

    def test_published_start_must_remain_in_future(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED)
        self.client.force_authenticate(self.organizer)

        response = self.client.patch(
            self.url(event),
            {"starts_at": (timezone.now() - timedelta(hours=1)).isoformat()},
        )

        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")
        self.assertIn("starts_at", response.data["error"]["details"])

    def test_past_draft_remains_editable(self):
        event = create_event(self.organizer, starts_at=timezone.now() - timedelta(days=1))
        self.client.force_authenticate(self.organizer)

        response = self.client.patch(
            self.url(event),
            {"starts_at": (timezone.now() + timedelta(days=14)).isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        event.refresh_from_db()
        self.assertFalse(event.has_started)

    def test_capacity_cannot_drop_below_confirmed_registrations(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED, capacity=5)
        create_registration(create_attendee("a@example.com"), event)
        create_registration(create_attendee("b@example.com"), event)
        self.client.force_authenticate(self.organizer)

        response = self.client.patch(self.url(event), {"capacity": 1})

        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="capacity_below_confirmed")
        event.refresh_from_db()
        self.assertEqual(event.capacity, 5)

    def test_capacity_can_be_reduced_to_confirmed_count(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED, capacity=5)
        create_registration(create_attendee("a@example.com"), event)
        create_registration(create_attendee("b@example.com"), event)
        self.client.force_authenticate(self.organizer)

        response = self.client.patch(self.url(event), {"capacity": 2})

        self.assertEqual(response.status_code, 200)
        event.refresh_from_db()
        self.assertEqual(event.capacity, 2)

    def test_cancelled_registrations_do_not_count_toward_capacity_floor(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED, capacity=5)
        create_registration(create_attendee("a@example.com"), event)
        create_registration(
            create_attendee("b@example.com"), event, status=RegistrationStatus.CANCELLED
        )
        self.client.force_authenticate(self.organizer)

        response = self.client.patch(self.url(event), {"capacity": 1})

        self.assertEqual(response.status_code, 200)
        event.refresh_from_db()
        self.assertEqual(event.capacity, 1)

    def test_put_is_not_allowed(self):
        event = create_event(self.organizer)
        self.client.force_authenticate(self.organizer)

        response = self.client.put(self.url(event), {"title": "PyCon"})

        self.assertEqual(response.status_code, 405)
        self.assertErrorEnvelope(response, code="method_not_allowed")
