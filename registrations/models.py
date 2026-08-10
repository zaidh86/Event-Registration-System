from django.conf import settings
from django.db import models


class RegistrationStatus(models.TextChoices):
    CONFIRMED = "CONFIRMED", "Confirmed"
    CANCELLED = "CANCELLED", "Cancelled"


class Registration(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="registrations"
    )
    event = models.ForeignKey(
        "events.Event", on_delete=models.PROTECT, related_name="registrations"
    )
    status = models.CharField(
        max_length=20,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.CONFIRMED,
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-registered_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "event"],
                condition=models.Q(status=RegistrationStatus.CONFIRMED),
                name="unique_confirmed_registration_per_user_and_event",
            )
        ]

    def __str__(self):
        return f"{self.user} @ {self.event} ({self.status})"
