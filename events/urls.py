from django.urls import path

from events.views import (
    EventCancelView,
    EventDetailView,
    EventListCreateView,
    EventPublishView,
    MyEventsView,
)

urlpatterns = [
    path("", EventListCreateView.as_view(), name="events-list"),
    path("mine/", MyEventsView.as_view(), name="events-mine"),
    path("<int:pk>/", EventDetailView.as_view(), name="events-detail"),
    path("<int:pk>/publish/", EventPublishView.as_view(), name="events-publish"),
    path("<int:pk>/cancel/", EventCancelView.as_view(), name="events-cancel"),
]
