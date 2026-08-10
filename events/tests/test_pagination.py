from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from common.testing import APITestCase
from events.models import Category, Event, EventStatus
from events.tests.helpers import create_organizer


def bulk_create_published_events(organizer, count):
    category = Category.objects.first()
    now = timezone.now()
    Event.objects.bulk_create(
        Event(
            organizer=organizer,
            title=f"Bulk Event {index:03d}",
            description="A bulk-created event.",
            category=category,
            location="Cairo",
            starts_at=now + timedelta(days=1, minutes=index),
            capacity=100,
            status=EventStatus.PUBLISHED,
        )
        for index in range(count)
    )


class EventListPaginationTests(APITestCase):
    url = reverse("events-list")

    def setUp(self):
        super().setUp()
        self.organizer = create_organizer()

    def test_default_page_size(self):
        bulk_create_published_events(self.organizer, 25)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(len(response.data["results"]), 20)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_second_page_returns_remainder(self):
        bulk_create_published_events(self.organizer, 25)

        response = self.client.get(self.url, {"page": 2})

        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNone(response.data["next"])
        self.assertIsNotNone(response.data["previous"])

    def test_custom_page_size(self):
        bulk_create_published_events(self.organizer, 25)

        response = self.client.get(self.url, {"page_size": 5})

        self.assertEqual(len(response.data["results"]), 5)
        self.assertEqual(response.data["count"], 25)

    def test_page_size_is_capped_at_maximum(self):
        bulk_create_published_events(self.organizer, 105)

        response = self.client.get(self.url, {"page_size": 500})

        self.assertEqual(len(response.data["results"]), 100)
        self.assertEqual(response.data["count"], 105)

    def test_invalid_page_returns_404(self):
        bulk_create_published_events(self.organizer, 5)

        for page in (99, 0, "abc"):
            response = self.client.get(self.url, {"page": page})
            self.assertEqual(response.status_code, 404)
            self.assertErrorEnvelope(response, code="not_found")

    def test_empty_result_set_returns_empty_first_page(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_pagination_combines_with_filters(self):
        bulk_create_published_events(self.organizer, 25)

        response = self.client.get(
            self.url, {"title": "Bulk Event", "page_size": 10, "page": 3}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(len(response.data["results"]), 5)
