"""Project-wide API error handling.

Every API error is returned in a single envelope:

    {"error": {"code": "<machine-readable>", "message": "<human-readable>", "details": <extra or null>}}
"""

import logging

from rest_framework.exceptions import ErrorDetail, Throttled, ValidationError
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)

CODE_OVERRIDES = {
    ValidationError: "validation_error",
}

GENERIC_MESSAGES = {
    ValidationError: "The request contains invalid data.",
}


def error_body(code, message, details=None):
    return {"error": {"code": code, "message": message, "details": details}}


def api_exception_handler(exc, context):
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
