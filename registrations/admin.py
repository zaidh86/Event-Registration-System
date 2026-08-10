from django.contrib import admin

from registrations.models import Registration


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "status", "registered_at", "cancelled_at")
    list_filter = ("status",)
    search_fields = ("user__email", "event__title")
    ordering = ("-registered_at",)
