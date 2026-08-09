from django.db import migrations

# Provisional list per PROJECT.md §16 (Categories); amendable in admin.
CATEGORY_NAMES = [
    "Business",
    "Conference",
    "Education",
    "Health",
    "Meetup",
    "Music",
    "Networking",
    "Sports",
    "Technology",
    "Workshop",
]


def seed_categories(apps, schema_editor):
    Category = apps.get_model("events", "Category")
    for name in CATEGORY_NAMES:
        Category.objects.get_or_create(name=name)


def remove_categories(apps, schema_editor):
    Category = apps.get_model("events", "Category")
    Category.objects.filter(name__in=CATEGORY_NAMES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_categories, remove_categories),
    ]
