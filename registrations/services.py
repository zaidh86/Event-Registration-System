"""Registration domain operations."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied

from common.exceptions import Conflict
from events.models import Event, EventStatus
from registrations.models import Registration, RegistrationStatus


def confirmed_registration_count(*, event):
    return Registration.objects.filter(
        event=event, status=RegistrationStatus.CONFIRMED
    ).count()


@transaction.atomic
def register_for_event(*, user, event_id):
    # The event-row lock serializes registrations per event, making the
    # count-then-insert capacity check safe under concurrent requests.
    try:
        event = Event.objects.select_for_update().get(pk=event_id)
    except Event.DoesNotExist:
        raise NotFound()
    if event.status == EventStatus.DRAFT and event.organizer_id != user.id:
        raise NotFound()
    if event.organizer_id == user.id:
        raise PermissionDenied("You cannot register for your own event.")
    if event.status != EventStatus.PUBLISHED:
        raise Conflict("The event is not open for registration.", code="event_not_open")
    if event.has_started:
        raise Conflict("The event has already started.", code="event_started")
    if Registration.objects.filter(
        event=event, user=user, status=RegistrationStatus.CONFIRMED
    ).exists():
        raise Conflict("You are already registered for this event.", code="already_registered")
    if confirmed_registration_count(event=event) >= event.capacity:
        raise Conflict("The event is at capacity.", code="event_full")
    return Registration.objects.create(user=user, event=event)


@transaction.atomic
def cancel_registration(*, user, registration_id):
    # Lock only the registration row: cancelling frees a seat, so it never
    # needs the event lock and cannot deadlock with registration creation.
    try:
        registration = (
            Registration.objects.select_for_update(of=("self",))
            .select_related("event")
            .get(pk=registration_id)
        )
    except Registration.DoesNotExist:
        raise NotFound()
    event = registration.event
    if registration.user_id != user.id and event.organizer_id != user.id:
        # Another user's registration is a private resource; hide it.
        raise NotFound()
    if registration.status != RegistrationStatus.CONFIRMED:
        raise Conflict("The registration is not active.", code="registration_not_active")
    if event.has_started:
        raise Conflict("The event has already started.", code="event_started")
    registration.status = RegistrationStatus.CANCELLED
    registration.cancelled_at = timezone.now()
    registration.save(update_fields=["status", "cancelled_at"])
    return registration
