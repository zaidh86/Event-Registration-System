"""Shared object factories for event tests."""

from datetime import timedelta

from django.utils import timezone

from events.models import Category, Event, EventStatus
from users import services
from users.models import UserRole


def create_organizer(email="organizer@example.com"):
    return services.create_user(
        email=email,
        password="correct-horse-battery",
        first_name="Grace",
        last_name="Hopper",
        role=UserRole.ORGANIZER,
    )


def create_attendee(email="attendee@example.com"):
    return services.create_user(
        email=email,
        password="correct-horse-battery",
        first_name="Ada",
        last_name="Lovelace",
        role=UserRole.ATTENDEE,
    )


def create_event(organizer, **overrides):
    fields = {
        "title": "Django Conference",
        "description": "A two-day conference about Django.",
        "category": Category.objects.first(),
        "location": "Cairo",
        "starts_at": timezone.now() + timedelta(days=7),
        "capacity": 100,
        "status": EventStatus.DRAFT,
    }
    fields.update(overrides)
    return Event.objects.create(organizer=organizer, **fields)
