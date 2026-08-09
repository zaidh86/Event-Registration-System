from django.contrib import admin
from django.urls import include, path

from events.views import CategoryListView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("authentication.urls")),
    path("api/v1/users/", include("users.urls")),
    path("api/v1/events/", include("events.urls")),
    path("api/v1/categories/", CategoryListView.as_view(), name="categories-list"),
]

handler400 = "common.views.bad_request"
handler404 = "common.views.not_found"
handler500 = "common.views.server_error"
