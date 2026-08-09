"""JSON handlers for errors raised outside of DRF views."""

from django.http import JsonResponse

from common.exceptions import error_body


def bad_request(request, exception=None):
    return JsonResponse(error_body("bad_request", "The request could not be understood."), status=400)


def not_found(request, exception=None):
    return JsonResponse(error_body("not_found", "The requested resource was not found."), status=404)


def server_error(request):
    return JsonResponse(error_body("server_error", "An unexpected error occurred."), status=500)
