"""User domain operations."""

from django.db import transaction
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from users.models import User


def create_user(*, email, password, first_name, last_name, role):
    return User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=role,
    )


@transaction.atomic
def change_password(*, user, new_password):
    user.set_password(new_password)
    user.save(update_fields=["password"])
    revoke_refresh_tokens(user)


def revoke_refresh_tokens(user):
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)
