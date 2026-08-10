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


class EventFilterSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    category = serializers.IntegerField(required=False, min_value=1)
    location = serializers.CharField(required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    upcoming = serializers.BooleanField(required=False)
    ordering = serializers.ChoiceField(
        required=False,
        choices=["starts_at", "-starts_at", "title", "-title", "created_at", "-created_at"],
    )


class DashboardEventSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    status = serializers.ChoiceField(choices=EventStatus.choices)
    starts_at = serializers.DateTimeField()
    capacity = serializers.IntegerField()
    confirmed_registrations = serializers.IntegerField()
    cancelled_registrations = serializers.IntegerField()
    available_seats = serializers.IntegerField()


class DashboardTotalsSerializer(serializers.Serializer):
    events = serializers.IntegerField()
    draft_events = serializers.IntegerField()
    published_events = serializers.IntegerField()
    cancelled_events = serializers.IntegerField()
    confirmed_registrations = serializers.IntegerField()
    cancelled_registrations = serializers.IntegerField()


class OrganizerDashboardSerializer(serializers.Serializer):
    totals = DashboardTotalsSerializer()
    events = DashboardEventSerializer(many=True)
