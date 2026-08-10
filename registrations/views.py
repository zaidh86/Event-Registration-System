from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from events import services as event_services
from registrations import services
from registrations.models import Registration
from registrations.serializers import RegistrationSerializer


class EventRegisterView(APIView):
    def post(self, request, pk):
        registration = services.register_for_event(user=request.user, event_id=pk)
        return Response(
            RegistrationSerializer(registration).data, status=status.HTTP_201_CREATED
        )


class RegistrationCancelView(APIView):
    def post(self, request, pk):
        registration = services.cancel_registration(user=request.user, registration_id=pk)
        return Response(RegistrationSerializer(registration).data)


class MyRegistrationsView(ListAPIView):
    serializer_class = RegistrationSerializer

    def get_queryset(self):
        return Registration.objects.filter(user=self.request.user).select_related(
            "event", "user"
        )


class EventRegistrationsView(ListAPIView):
    serializer_class = RegistrationSerializer

    def get_queryset(self):
        event = event_services.get_owned_event(user=self.request.user, pk=self.kwargs["pk"])
        return Registration.objects.filter(event=event).select_related("event", "user")
