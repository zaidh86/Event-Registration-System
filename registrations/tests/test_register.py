from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from common.testing import APITestCase
from events.models import EventStatus
from events.tests.helpers import create_attendee, create_event, create_organizer
from registrations.models import Registration, RegistrationStatus
from registrations.tests.helpers import create_registration


class RegisterTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.organizer = create_organizer()
        self.attendee = create_attendee()
        self.event = create_event(self.organizer, status=EventStatus.PUBLISHED)

    def url(self, event):
        return reverse("events-register", args=[event.id])

    def test_attendee_registers_successfully(self):
        self.client.force_authenticate(self.attendee)

        response = self.client.post(self.url(self.event))

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], RegistrationStatus.CONFIRMED)
        self.assertIsNone(response.data["cancelled_at"])
        self.assertEqual(response.data["event"]["id"], self.event.id)
        self.assertEqual(response.data["event"]["status"], EventStatus.PUBLISHED)
        self.assertEqual(response.data["user"]["id"], self.attendee.id)
        self.assertEqual(
            Registration.objects.filter(
                event=self.event, user=self.attendee, status=RegistrationStatus.CONFIRMED
            ).count(),
            1,
        )

    def test_requires_authentication(self):
        response = self.client.post(self.url(self.event))

        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")

    def test_duplicate_registration_is_rejected(self):
        create_registration(self.attendee, self.event)
        self.client.force_authenticate(self.attendee)

        response = self.client.post(self.url(self.event))

        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="already_registered")

    def test_reregistration_after_cancellation_creates_new_record(self):
        create_registration(self.attendee, self.event, status=RegistrationStatus.CANCELLED)
        self.client.force_authenticate(self.attendee)

        response = self.client.post(self.url(self.event))

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            Registration.objects.filter(event=self.event, user=self.attendee).count(), 2
        )

    def test_registration_fills_the_last_seat(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED, capacity=2)
        create_registration(create_attendee("first@example.com"), event)
        self.client.force_authenticate(self.attendee)

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 201)

    def test_full_event_is_rejected(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED, capacity=1)
        create_registration(create_attendee("first@example.com"), event)
        self.client.force_authenticate(self.attendee)

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="event_full")

    def test_cancelled_registrations_do_not_consume_capacity(self):
        event = create_event(self.organizer, status=EventStatus.PUBLISHED, capacity=1)
        create_registration(
            create_attendee("first@example.com"), event, status=RegistrationStatus.CANCELLED
        )
        self.client.force_authenticate(self.attendee)

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 201)

    def test_cancelled_event_is_rejected(self):
        event = create_event(self.organizer, status=EventStatus.CANCELLED)
        self.client.force_authenticate(self.attendee)

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="event_not_open")

    def test_draft_event_is_hidden(self):
        event = create_event(self.organizer)
        self.client.force_authenticate(self.attendee)

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 404)
        self.assertErrorEnvelope(response, code="not_found")

    def test_past_event_is_rejected(self):
        event = create_event(
            self.organizer,
            status=EventStatus.PUBLISHED,
            starts_at=timezone.now() - timedelta(hours=1),
        )
        self.client.force_authenticate(self.attendee)

        response = self.client.post(self.url(event))

        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="event_started")

    def test_missing_event_returns_404(self):
        self.client.force_authenticate(self.attendee)

        response = self.client.post(reverse("events-register", args=[999999]))

        self.assertEqual(response.status_code, 404)
        self.assertErrorEnvelope(response, code="not_found")

    def test_organizer_cannot_register_for_own_event(self):
        self.client.force_authenticate(self.organizer)

        response = self.client.post(self.url(self.event))

        self.assertEqual(response.status_code, 403)
        self.assertErrorEnvelope(response, code="permission_denied")

    def test_organizer_can_register_for_another_organizers_event(self):
        other_organizer = create_organizer("other@example.com")
        self.client.force_authenticate(other_organizer)

        response = self.client.post(self.url(self.event))

        self.assertEqual(response.status_code, 201)
