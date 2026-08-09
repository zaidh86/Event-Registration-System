"""Project-wide API error handling.

Every API error is returned in a single envelope:

    {"error": {"code": "<machine-readable>", "message": "<human-readable>", "details": <extra or null>}}
"""

import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    ErrorDetail,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


class Conflict(APIException):
    """The request is valid but conflicts with the current resource state."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "The request conflicts with the current state of the resource."
    default_code = "conflict"

CODE_OVERRIDES = {
    ValidationError: "validation_error",
}

GENERIC_MESSAGES = {
    ValidationError: "The request contains invalid data.",
}


def error_body(code, message, details=None):
    return {"error": {"code": code, "message": message, "details": details}}


def api_exception_handler(exc, context):
    # Mirror DRF's own conversion of Django exceptions so the envelope
    # logic below always operates on a DRF exception.
    if isinstance(exc, Http404):
        exc = NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = PermissionDenied()

    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    detail = getattr(exc, "detail", None)

    if type(exc) in CODE_OVERRIDES:
        code = CODE_OVERRIDES[type(exc)]
    elif isinstance(detail, ErrorDetail):
        # A code passed at raise time (e.g. Simple JWT's "no_active_account")
        # is more specific than the exception's class-level default_code.
        code = detail.code
    else:
        code = getattr(exc, "default_code", "error")

    if isinstance(detail, dict) and "detail" in detail:
        # Some exceptions (e.g. Simple JWT token errors) carry a dict detail
        # with the human-readable message under the "detail" key.
        message = str(detail["detail"])
        details = {key: value for key, value in detail.items() if key != "detail"} or None
    elif isinstance(detail, (dict, list)):
        message = GENERIC_MESSAGES.get(type(exc), "The request could not be processed.")
        details = detail
    else:
        message = str(detail)
        details = None

    if isinstance(exc, Throttled) and exc.wait is not None:
        details = {"wait_seconds": int(exc.wait)}

    if response.status_code >= 500:
        logger.error("Unhandled API error in %s: %s", context.get("view"), exc)

    response.data = error_body(code, message, details)
    return response
