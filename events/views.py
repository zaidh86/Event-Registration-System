from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from events import services
from events.models import Category, Event, EventStatus
from events.permissions import IsOrganizer
from events.serializers import (
    CategorySerializer,
    EventFilterSerializer,
    EventSerializer,
    OrganizerDashboardSerializer,
)


class CategoryListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()


@extend_schema_view(get=extend_schema(parameters=[EventFilterSerializer]))
class EventListCreateView(ListCreateAPIView):
    serializer_class = EventSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsOrganizer()]
        return [AllowAny()]

    def get_queryset(self):
        filter_serializer = EventFilterSerializer(data=self.request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        return services.search_published_events(filters=filter_serializer.validated_data)

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)


class MyEventsView(ListAPIView):
    permission_classes = [IsOrganizer]
    serializer_class = EventSerializer

    def get_queryset(self):
        return Event.objects.filter(organizer=self.request.user).select_related("category")


class EventDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = EventSerializer
    http_method_names = ["get", "patch", "delete", "head", "options"]
    queryset = Event.objects.select_related("category")

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_object(self):
        if self.request.method in SAFE_METHODS:
            event = super().get_object()
            if (
                event.status == EventStatus.DRAFT
                and event.organizer_id != getattr(self.request.user, "id", None)
            ):
                # Draft events are invisible to everyone but their organizer.
                raise NotFound()
            return event

        event = services.get_owned_event(user=self.request.user, pk=self.kwargs["pk"])
        if self.request.method == "PATCH":
            services.ensure_event_editable(event=event)
        return event

    def perform_update(self, serializer):
        # Lock the event row so the capacity floor cannot be bypassed by a
        # registration committing between the check and the save.
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=serializer.instance.pk)
            services.ensure_capacity_not_below_confirmed(
                event=event, new_capacity=serializer.validated_data.get("capacity")
            )
            serializer.save()

    def perform_destroy(self, instance):
        services.delete_event(event=instance)


class EventPublishView(APIView):
    @extend_schema(request=None, responses=EventSerializer)
    def post(self, request, pk):
        event = services.get_owned_event(user=request.user, pk=pk)
        services.publish_event(event=event)
        return Response(EventSerializer(event).data)


class EventCancelView(APIView):
    @extend_schema(request=None, responses=EventSerializer)
    def post(self, request, pk):
        event = services.get_owned_event(user=request.user, pk=pk)
        services.cancel_event(event=event)
        return Response(EventSerializer(event).data)


class OrganizerDashboardView(APIView):
    permission_classes = [IsOrganizer]

    @extend_schema(responses=OrganizerDashboardSerializer)
    def get(self, request):
        dashboard = services.organizer_dashboard(organizer=request.user)
        return Response(OrganizerDashboardSerializer(dashboard).data)
