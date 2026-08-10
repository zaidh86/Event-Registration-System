from django.urls import path

from registrations.views import (
    EventRegisterView,
    EventRegistrationsView,
    MyRegistrationsView,
    RegistrationCancelView,
)

urlpatterns = [
    path("events/<int:pk>/register/", EventRegisterView.as_view(), name="events-register"),
    path(
        "events/<int:pk>/registrations/",
        EventRegistrationsView.as_view(),
        name="events-registrations",
    ),
    path("registrations/", MyRegistrationsView.as_view(), name="registrations-list"),
    path(
        "registrations/<int:pk>/cancel/",
        RegistrationCancelView.as_view(),
        name="registrations-cancel",
    ),
]
