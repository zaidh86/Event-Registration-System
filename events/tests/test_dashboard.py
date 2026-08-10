from django.urls import reverse

from common.testing import APITestCase
from events import services
from events.models import EventStatus
from events.tests.helpers import create_attendee, create_event, create_organizer
from registrations.models import RegistrationStatus
from registrations.tests.helpers import create_registration


class OrganizerDashboardTests(APITestCase):
    url = reverse("organizer-dashboard")

    def setUp(self):
        super().setUp()
        self.organizer = create_organizer()

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertErrorEnvelope(response, code="not_authenticated")

    def test_attendee_is_forbidden(self):
        self.client.force_authenticate(create_attendee())

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertErrorEnvelope(response, code="permission_denied")

    def test_totals_and_per_event_aggregates(self):
        published = create_event(
            self.organizer, title="Published", status=EventStatus.PUBLISHED, capacity=10
        )
        draft = create_event(self.organizer, title="Draft")
        create_event(self.organizer, title="Cancelled", status=EventStatus.CANCELLED)
        create_registration(create_attendee("a@example.com"), published)
        create_registration(create_attendee("b@example.com"), published)
        create_registration(
            create_attendee("c@example.com"),
            published,
            status=RegistrationStatus.CANCELLED,
        )
        self.client.force_authenticate(self.organizer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["totals"],
            {
                "events": 3,
                "draft_events": 1,
                "published_events": 1,
                "cancelled_events": 1,
                "confirmed_registrations": 2,
                "cancelled_registrations": 1,
            },
        )
        rows = {row["id"]: row for row in response.data["events"]}
        self.assertEqual(rows[published.id]["confirmed_registrations"], 2)
        self.assertEqual(rows[published.id]["cancelled_registrations"], 1)
        self.assertEqual(rows[published.id]["available_seats"], 8)
        self.assertEqual(rows[draft.id]["confirmed_registrations"], 0)
        self.assertEqual(rows[draft.id]["available_seats"], draft.capacity)

    def test_response_shape(self):
        create_event(self.organizer, status=EventStatus.PUBLISHED)
        self.client.force_authenticate(self.organizer)

        response = self.client.get(self.url)

        self.assertEqual(set(response.data), {"totals", "events"})
        row = response.data["events"][0]
        self.assertEqual(
            set(row),
            {
                "id",
                "title",
                "status",
                "starts_at",
                "capacity",
                "confirmed_registrations",
                "cancelled_registrations",
                "available_seats",
            },
        )

    def test_scoped_to_requesting_organizer(self):
        other_organizer = create_organizer("other@example.com")
        other_event = create_event(other_organizer, status=EventStatus.PUBLISHED)
        create_registration(create_attendee(), other_event)
        mine = create_event(self.organizer)
        self.client.force_authenticate(self.organizer)

        response = self.client.get(self.url)

        self.assertEqual([row["id"] for row in response.data["events"]], [mine.id])
        self.assertEqual(response.data["totals"]["events"], 1)
        self.assertEqual(response.data["totals"]["confirmed_registrations"], 0)

    def test_dashboard_uses_a_single_query(self):
        create_event(self.organizer, status=EventStatus.PUBLISHED)
        create_event(self.organizer, title="Second")

        with self.assertNumQueries(1):
            services.organizer_dashboard(organizer=self.organizer)
