from django.utils import timezone
from rest_framework import serializers

from events.models import Category, Event, EventStatus


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id",
            "organizer",
            "title",
            "description",
            "category",
            "location",
            "starts_at",
            "capacity",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organizer", "status", "created_at", "updated_at"]
        extra_kwargs = {"capacity": {"min_value": 1}}

    def validate_starts_at(self, value):
        published = self.instance is not None and self.instance.status == EventStatus.PUBLISHED
        if published and value <= timezone.now():
            raise serializers.ValidationError(
                "A published event must keep its start date/time in the future."
            )
        return value
