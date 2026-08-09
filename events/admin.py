from django.contrib import admin

from events.models import Category, Event


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "organizer", "category", "status", "starts_at", "capacity")
    list_filter = ("status", "category")
    search_fields = ("title", "location", "organizer__email")
    ordering = ("-starts_at",)
