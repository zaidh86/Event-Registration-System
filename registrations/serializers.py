from rest_framework import serializers

from events.models import Event
from registrations.models import Registration
from users.models import User


class RegistrationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["id", "title", "location", "starts_at", "status"]


class RegistrationUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class RegistrationSerializer(serializers.ModelSerializer):
    event = RegistrationEventSerializer(read_only=True)
    user = RegistrationUserSerializer(read_only=True)

    class Meta:
        model = Registration
        fields = ["id", "user", "event", "status", "registered_at", "cancelled_at"]
        read_only_fields = fields
