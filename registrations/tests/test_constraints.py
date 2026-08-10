from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from common.testing import APITestCase
from events.models import EventStatus
from events.tests.helpers import create_attendee, create_event, create_organizer
from registrations.models import Registration, RegistrationStatus
from registrations.tests.helpers import create_registration


class RegistrationConstraintTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.organizer = create_organizer()
        self.attendee = create_attendee()
        self.event = create_event(self.organizer, status=EventStatus.PUBLISHED)

    def test_database_rejects_duplicate_confirmed_registration(self):
        create_registration(self.attendee, self.event)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Registration.objects.create(user=self.attendee, event=self.event)

    def test_database_allows_new_confirmed_after_cancellation(self):
        create_registration(self.attendee, self.event, status=RegistrationStatus.CANCELLED)

        registration = Registration.objects.create(user=self.attendee, event=self.event)

        self.assertEqual(registration.status, RegistrationStatus.CONFIRMED)

    def test_database_allows_multiple_cancelled_registrations(self):
        create_registration(self.attendee, self.event, status=RegistrationStatus.CANCELLED)
        create_registration(self.attendee, self.event, status=RegistrationStatus.CANCELLED)

        self.assertEqual(
            Registration.objects.filter(user=self.attendee, event=self.event).count(), 2
        )

    def test_database_protects_event_with_registrations_from_deletion(self):
        create_registration(self.attendee, self.event)

        with self.assertRaises(ProtectedError), transaction.atomic():
            self.event.delete()
