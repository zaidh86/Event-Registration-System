"""Shared object factories for registration tests."""

from django.utils import timezone

from registrations.models import Registration, RegistrationStatus


def create_registration(user, event, status=RegistrationStatus.CONFIRMED):
    cancelled_at = timezone.now() if status == RegistrationStatus.CANCELLED else None
    return Registration.objects.create(
        user=user, event=event, status=status, cancelled_at=cancelled_at
    )
