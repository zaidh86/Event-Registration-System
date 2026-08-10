from django.urls import reverse

from common.testing import APITestCase
from events.models import EventStatus
from events.tests.helpers import create_attendee, create_event, create_organizer
from registrations.models import RegistrationStatus
from registrations.tests.helpers import create_registration


class EventRegistrationsListTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.organizer = create_organizer()
        self.event = create_event(self.organizer, status=EventStatus.PUBLISHED)

    def url(self, event):
        return reverse("events-registrations", args=[event.id])

    def test_owner_lists_registrations_of_every_status(self):
        confirmed = create_registration(create_attendee("a@example.com"), self.event)
        cancelled = create_registration(
            create_attendee("b@example.com"), self.event, status=RegistrationStatus.CANCELLED
        )
        create_registration(
            create_attendee("c@example.com"),
            create_event(self.organizer, title="Other", status=EventStatus.PUBLISHED),
        )
        self.client.force_authenticate(self.organizer)

        response = self.client.get(self.url(self.event))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        ids = {item["id"] for item in response.data["results"]}
        self.assertEqual(ids, {confirmed.id, cancelled.id})
        emails = {item["user"]["email"] for item in response.data["results"]}
        self.assertEqual(emails, {"a@example.com", "b@example.com"})

    def test_requires_authentication(self):
        response = self.client.get(self.url(self.event))

        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")

    def test_attendee_is_forbidden(self):
        self.client.force_authenticate(create_attendee())

        response = self.client.get(self.url(self.event))

        self.assertEqual(response.status_code, 403)
        self.assertErrorEnvelope(response, code="permission_denied")

    def test_other_organizer_is_forbidden(self):
        self.client.force_authenticate(create_organizer("other@example.com"))

        response = self.client.get(self.url(self.event))

        self.assertEqual(response.status_code, 403)
        self.assertErrorEnvelope(response, code="permission_denied")

    def test_other_users_get_404_for_draft_event(self):
        draft = create_event(self.organizer)
        self.client.force_authenticate(create_organizer("other@example.com"))

        response = self.client.get(self.url(draft))

        self.assertEqual(response.status_code, 404)
        self.assertErrorEnvelope(response, code="not_found")
