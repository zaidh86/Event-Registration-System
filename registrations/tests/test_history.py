from django.urls import reverse

from common.testing import APITestCase
from events.models import EventStatus
from events.tests.helpers import create_attendee, create_event, create_organizer
from events import services as event_services
from registrations.models import RegistrationStatus
from registrations.tests.helpers import create_registration


class RegistrationHistoryTests(APITestCase):
    url = reverse("registrations-list")

    def setUp(self):
        super().setUp()
        self.organizer = create_organizer()
        self.attendee = create_attendee()
        self.event = create_event(self.organizer, status=EventStatus.PUBLISHED)

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")

    def test_lists_only_own_registrations_of_every_status(self):
        confirmed = create_registration(self.attendee, self.event)
        other_event = create_event(
            self.organizer, title="Other", status=EventStatus.PUBLISHED
        )
        cancelled = create_registration(
            self.attendee, other_event, status=RegistrationStatus.CANCELLED
        )
        create_registration(create_attendee("other@example.com"), self.event)
        self.client.force_authenticate(self.attendee)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        ids = {item["id"] for item in response.data["results"]}
        self.assertEqual(ids, {confirmed.id, cancelled.id})

    def test_response_shape_embeds_event_and_user(self):
        create_registration(self.attendee, self.event)
        self.client.force_authenticate(self.attendee)

        response = self.client.get(self.url)

        item = response.data["results"][0]
        self.assertEqual(
            set(item), {"id", "user", "event", "status", "registered_at", "cancelled_at"}
        )
        self.assertEqual(
            set(item["event"]), {"id", "title", "location", "starts_at", "status"}
        )
        self.assertEqual(set(item["user"]), {"id", "email", "first_name", "last_name"})

    def test_event_cancellation_is_reflected_without_modifying_registration(self):
        registration = create_registration(self.attendee, self.event)
        event_services.cancel_event(event=self.event)
        self.client.force_authenticate(self.attendee)

        response = self.client.get(self.url)

        item = response.data["results"][0]
        self.assertEqual(item["id"], registration.id)
        self.assertEqual(item["status"], RegistrationStatus.CONFIRMED)
        self.assertEqual(item["event"]["status"], EventStatus.CANCELLED)

    def test_response_is_paginated(self):
        self.client.force_authenticate(self.attendee)

        response = self.client.get(self.url)

        self.assertEqual(set(response.data), {"count", "next", "previous", "results"})
