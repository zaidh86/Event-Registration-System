from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from common.testing import APITestCase
from events.models import Category, EventStatus
from events.tests.helpers import create_event, create_organizer


class EventSearchTests(APITestCase):
    url = reverse("events-list")

    def setUp(self):
        super().setUp()
        self.organizer = create_organizer()
        self.tech = Category.objects.get(name="Technology")
        self.music = Category.objects.get(name="Music")
        self.django_conf = create_event(
            self.organizer,
            title="Django Conference",
            location="Cairo",
            category=self.tech,
            status=EventStatus.PUBLISHED,
            starts_at=timezone.now() + timedelta(days=10),
        )
        self.jazz_night = create_event(
            self.organizer,
            title="Jazz Night",
            location="Alexandria",
            category=self.music,
            status=EventStatus.PUBLISHED,
            starts_at=timezone.now() + timedelta(days=30),
        )

    def result_ids(self, response):
        return {item["id"] for item in response.data["results"]}

    def test_filters_by_title_case_insensitively(self):
        response = self.client.get(self.url, {"title": "django"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.result_ids(response), {self.django_conf.id})

    def test_filters_by_category(self):
        response = self.client.get(self.url, {"category": self.music.id})

        self.assertEqual(self.result_ids(response), {self.jazz_night.id})

    def test_unknown_category_returns_empty_results(self):
        response = self.client.get(self.url, {"category": 999999})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_filters_by_location_case_insensitively(self):
        response = self.client.get(self.url, {"location": "cairo"})

        self.assertEqual(self.result_ids(response), {self.django_conf.id})

    def test_filters_by_date_range(self):
        pivot = (timezone.now() + timedelta(days=20)).isoformat()

        from_response = self.client.get(self.url, {"date_from": pivot})
        to_response = self.client.get(self.url, {"date_to": pivot})

        self.assertEqual(self.result_ids(from_response), {self.jazz_night.id})
        self.assertEqual(self.result_ids(to_response), {self.django_conf.id})

    def test_upcoming_excludes_started_events(self):
        started = create_event(
            self.organizer,
            title="Started Meetup",
            status=EventStatus.PUBLISHED,
            starts_at=timezone.now() - timedelta(hours=1),
        )

        unfiltered = self.client.get(self.url)
        upcoming = self.client.get(self.url, {"upcoming": "true"})

        self.assertIn(started.id, self.result_ids(unfiltered))
        self.assertEqual(
            self.result_ids(upcoming), {self.django_conf.id, self.jazz_night.id}
        )

    def test_filters_combine_with_and(self):
        mismatched = self.client.get(self.url, {"title": "night", "category": self.tech.id})
        matched = self.client.get(self.url, {"title": "night", "category": self.music.id})

        self.assertEqual(mismatched.data["count"], 0)
        self.assertEqual(self.result_ids(matched), {self.jazz_night.id})

    def test_ordering_by_start_descending(self):
        response = self.client.get(self.url, {"ordering": "-starts_at"})

        ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(ids, [self.jazz_night.id, self.django_conf.id])

    def test_search_never_returns_drafts_or_cancelled_events(self):
        create_event(self.organizer, title="Django Sprint")
        create_event(
            self.organizer, title="Django Workshop", status=EventStatus.CANCELLED
        )

        response = self.client.get(self.url, {"title": "django"})

        self.assertEqual(self.result_ids(response), {self.django_conf.id})

    def test_invalid_date_returns_validation_error(self):
        response = self.client.get(self.url, {"date_from": "not-a-date"})

        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")
        self.assertIn("date_from", response.data["error"]["details"])

    def test_invalid_upcoming_returns_validation_error(self):
        response = self.client.get(self.url, {"upcoming": "maybe"})

        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")
        self.assertIn("upcoming", response.data["error"]["details"])

    def test_invalid_ordering_returns_validation_error(self):
        response = self.client.get(self.url, {"ordering": "capacity"})

        self.assertEqual(response.status_code, 400)
        self.assertErrorEnvelope(response, code="validation_error")
        self.assertIn("ordering", response.data["error"]["details"])
