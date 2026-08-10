from django.urls import reverse

from common.testing import APITestCase
from events.models import Event, EventStatus
from events.tests.helpers import create_attendee, create_event, create_organizer
from registrations.models import RegistrationStatus
from registrations.tests.helpers import create_registration


class EventDeleteTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.organizer = create_organizer()

    def url(self, event):
        return reverse("events-detail", args=[event.id])

    def test_owner_deletes_event(self):
        event = create_event(self.organizer)
        self.client.force_authenticate(self.organizer)

        response = self.client.delete(self.url(event))

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Event.objects.filter(id=event.id).exists())

    def test_requires_authentication(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED)

        response = self.client.delete(self.url(event))

        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")

    def test_non_owner_cannot_delete_visible_event(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED)
        self.client.force_authenticate(create_organizer("other@example.com"))

        response = self.client.delete(self.url(event))

        self.assertEqual(response.status_code, 403)
        self.assertErrorEnvelope(response, code="permission_denied")

    def test_non_owner_gets_404_for_draft(self):
        event = create_event(self.organizer)
        self.client.force_authenticate(create_organizer("other@example.com"))

        response = self.client.delete(self.url(event))

        self.assertEqual(response.status_code, 404)
        self.assertErrorEnvelope(response, code="not_found")

    def test_event_with_registrations_cannot_be_deleted(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED)
        create_registration(create_attendee(), event)
        self.client.force_authenticate(self.organizer)

        response = self.client.delete(self.url(event))

        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="event_has_registrations")
        self.assertTrue(Event.objects.filter(id=event.id).exists())

    def test_event_with_only_cancelled_registrations_cannot_be_deleted(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED)
        create_registration(
            create_attendee(), event, status=RegistrationStatus.CANCELLED
        )
        self.client.force_authenticate(self.organizer)

        response = self.client.delete(self.url(event))

        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="event_has_registrations")
