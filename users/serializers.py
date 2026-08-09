from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "role", "date_joined"]
        read_only_fields = ["id", "email", "role", "date_joined"]
