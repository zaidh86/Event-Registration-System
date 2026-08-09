"""Event domain operations."""

from rest_framework.exceptions import NotFound, PermissionDenied

from common.exceptions import Conflict
from events.models import Event, EventStatus


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
