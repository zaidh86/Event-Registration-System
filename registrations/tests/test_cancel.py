from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from common.testing import APITestCase
from events.models import EventStatus
from events.tests.helpers import create_attendee, create_event, create_organizer
from registrations.models import RegistrationStatus
from registrations.tests.helpers import create_registration


class CancelRegistrationTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.organizer = create_organizer()
        self.attendee = create_attendee()
        self.event = create_event(self.organizer, status=EventStatus.PUBLISHED)
        self.registration = create_registration(self.attendee, self.event)

    def url(self, registration):
        return reverse("registrations-cancel", args=[registration.id])

    def test_attendee_cancels_own_registration(self):
        self.client.force_authenticate(self.attendee)

        response = self.client.post(self.url(self.registration))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], RegistrationStatus.CANCELLED)
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, RegistrationStatus.CANCELLED)
        self.assertIsNotNone(self.registration.cancelled_at)

    def test_requires_authentication(self):
        response = self.client.post(self.url(self.registration))

        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")

    def test_other_user_gets_404(self):
        self.client.force_authenticate(create_attendee("other@example.com"))

        response = self.client.post(self.url(self.registration))

        self.assertEqual(response.status_code, 404)
        self.assertErrorEnvelope(response, code="not_found")

    def test_unrelated_organizer_gets_404(self):
        self.client.force_authenticate(create_organizer("other@example.com"))

        response = self.client.post(self.url(self.registration))

        self.assertEqual(response.status_code, 404)
        self.assertErrorEnvelope(response, code="not_found")

    def test_event_organizer_cancels_attendee_registration(self):
        self.client.force_authenticate(self.organizer)

        response = self.client.post(self.url(self.registration))

        self.assertEqual(response.status_code, 200)
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, RegistrationStatus.CANCELLED)

    def test_already_cancelled_registration_is_rejected(self):
        registration = create_registration(
            create_attendee("other@example.com"), self.event, status=RegistrationStatus.CANCELLED
        )
        self.client.force_authenticate(self.organizer)

        response = self.client.post(self.url(registration))

        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="registration_not_active")

    def test_cancellation_after_event_start_is_rejected(self):
        event = create_event(
            self.organizer,
            status=EventStatus.PUBLISHED,
            starts_at=timezone.now() + timedelta(hours=1),
        )
        registration = create_registration(self.attendee, event)
        event.starts_at = timezone.now() - timedelta(minutes=5)
        event.save(update_fields=["starts_at"])
        self.client.force_authenticate(self.attendee)

        response = self.client.post(self.url(registration))

        self.assertEqual(response.status_code, 409)
        self.assertErrorEnvelope(response, code="event_started")

    def test_missing_registration_returns_404(self):
        self.client.force_authenticate(self.attendee)

        response = self.client.post(reverse("registrations-cancel", args=[999999]))

        self.assertEqual(response.status_code, 404)
        self.assertErrorEnvelope(response, code="not_found")
