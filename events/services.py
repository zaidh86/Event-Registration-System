"""Event domain operations."""

from django.db import transaction
from rest_framework.exceptions import NotFound, PermissionDenied

from common.exceptions import Conflict
from events.models import Event, EventStatus
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
