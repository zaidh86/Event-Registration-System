"""Event domain operations."""

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied

from common.exceptions import Conflict
from events.models import Event, EventStatus
from registrations.models import RegistrationStatus
from registrations.services import confirmed_registration_count


def get_owned_event(*, user, pk):
    """Fetch an event for modification by its organizer.

    Invisible events (missing, or another user's draft) yield 404; visible
    events owned by someone else yield 403.
    """
    try:
        event = Event.objects.select_related("category").get(pk=pk)
    except Event.DoesNotExist:
        raise NotFound()
    if event.status == EventStatus.DRAFT and event.organizer_id != user.id:
        raise NotFound()
    if event.organizer_id != user.id:
        raise PermissionDenied("You may only manage your own events.")
    return event


def ensure_event_editable(*, event):
    # Draft events are freely editable, including drafts whose start has
    # passed — otherwise a stale draft could never be rescheduled.
    if event.status == EventStatus.CANCELLED:
        raise Conflict("A cancelled event cannot be edited.", code="event_not_editable")
    if event.status == EventStatus.PUBLISHED and event.has_started:
        raise Conflict("A past event cannot be edited.", code="event_not_editable")


def publish_event(*, event):
    if event.status != EventStatus.DRAFT:
        raise Conflict("Only draft events can be published.", code="invalid_status_transition")
    if event.has_started:
        raise Conflict(
            "An event must start in the future to be published.", code="event_start_in_past"
        )
    event.status = EventStatus.PUBLISHED
    event.save(update_fields=["status", "updated_at"])
    return event


def cancel_event(*, event):
    if event.status != EventStatus.PUBLISHED:
        raise Conflict("Only published events can be cancelled.", code="invalid_status_transition")
    event.status = EventStatus.CANCELLED
    event.save(update_fields=["status", "updated_at"])
    return event


@transaction.atomic
def delete_event(*, event):
    # The event-row lock serializes deletion against concurrent registration
    # creation; the PROTECT foreign key is the database backstop.
    locked_event = Event.objects.select_for_update().get(pk=event.pk)
    if locked_event.registrations.exists():
        raise Conflict(
            "An event with registrations cannot be deleted; cancel it instead.",
            code="event_has_registrations",
        )
    locked_event.delete()


def ensure_capacity_not_below_confirmed(*, event, new_capacity):
    """Enforce the published-event capacity floor.

    Must be called with the event row locked so the confirmed count cannot
    grow between the check and the save.
    """
    if new_capacity is None or event.status != EventStatus.PUBLISHED:
        return
    if new_capacity < confirmed_registration_count(event=event):
        raise Conflict(
            "Capacity cannot be reduced below the number of confirmed registrations.",
            code="capacity_below_confirmed",
        )


def search_published_events(*, filters):
    """Filter the public event list; all filters combine with AND."""
    queryset = Event.objects.filter(status=EventStatus.PUBLISHED).select_related("category")
    if title := filters.get("title"):
        queryset = queryset.filter(title__icontains=title)
    if (category := filters.get("category")) is not None:
        queryset = queryset.filter(category_id=category)
    if location := filters.get("location"):
        queryset = queryset.filter(location__icontains=location)
    if date_from := filters.get("date_from"):
        queryset = queryset.filter(starts_at__gte=date_from)
    if date_to := filters.get("date_to"):
        queryset = queryset.filter(starts_at__lte=date_to)
    if filters.get("upcoming"):
        queryset = queryset.filter(starts_at__gt=timezone.now())
    if ordering := filters.get("ordering"):
        queryset = queryset.order_by(ordering, "id")
    return queryset


def organizer_dashboard(*, organizer):
    events = list(
        Event.objects.filter(organizer=organizer).annotate(
            confirmed_registrations=Count(
                "registrations",
                filter=Q(registrations__status=RegistrationStatus.CONFIRMED),
            ),
            cancelled_registrations=Count(
                "registrations",
                filter=Q(registrations__status=RegistrationStatus.CANCELLED),
            ),
        )
    )
    for event in events:
        event.available_seats = max(event.capacity - event.confirmed_registrations, 0)
    status_counts = {
        status: sum(1 for event in events if event.status == status)
        for status in (EventStatus.DRAFT, EventStatus.PUBLISHED, EventStatus.CANCELLED)
    }
    totals = {
        "events": len(events),
        "draft_events": status_counts[EventStatus.DRAFT],
        "published_events": status_counts[EventStatus.PUBLISHED],
        "cancelled_events": status_counts[EventStatus.CANCELLED],
        "confirmed_registrations": sum(event.confirmed_registrations for event in events),
        "cancelled_registrations": sum(event.cancelled_registrations for event in events),
    }
    return {"totals": totals, "events": events}
