from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from events.views import CategoryListView, OrganizerDashboardView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("authentication.urls")),
    path("api/v1/users/", include("users.urls")),
    path("api/v1/events/", include("events.urls")),
    path("api/v1/categories/", CategoryListView.as_view(), name="categories-list"),
    path("api/v1/organizer/dashboard/", OrganizerDashboardView.as_view(), name="organizer-dashboard"),
    path("api/v1/", include("registrations.urls")),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

handler400 = "common.views.bad_request"
handler404 = "common.views.not_found"
handler500 = "common.views.server_error"
