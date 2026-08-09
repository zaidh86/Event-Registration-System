from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from common.testing import APITestCase
from events.models import EventStatus
from events.tests.helpers import create_event, create_organizer


class EventListTests(APITestCase):
    url = reverse("events-list")

    def setUp(self):
        super().setUp()
        self.organizer = create_organizer()
        self.published = create_event(
            self.organizer, title="Published", status=EventStatus.PUBLISHED
        )
        create_event(self.organizer, title="Draft")
        create_event(self.organizer, title="Cancelled", status=EventStatus.CANCELLED)

    def test_lists_only_published_events_publicly(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.published.id)

    def test_response_is_paginated(self):
        response = self.client.get(self.url)

        self.assertEqual(set(response.data), {"count", "next", "previous", "results"})

    def test_orders_by_start_time(self):
        later = create_event(
            self.organizer,
            title="Later",
            status=EventStatus.PUBLISHED,
            starts_at=timezone.now() + timedelta(days=30),
        )
        sooner = create_event(
            self.organizer,
            title="Sooner",
            status=EventStatus.PUBLISHED,
            starts_at=timezone.now() + timedelta(days=1),
        )

        response = self.client.get(self.url)

        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [sooner.id, self.published.id, later.id])
