"""Small, composable pieces reused across userapp views to avoid repeating
the same "fetch this object but scoped to the current user" and "return a
consistent AJAX JSON envelope" patterns in every view."""
from django.http import JsonResponse
from django.shortcuts import get_object_or_404


def get_owned_or_404(model, request, **extra_filters):
    """``get_object_or_404`` pre-scoped to objects the current user owns.

    Example: ``get_owned_or_404(Order, request, pk=pk, customer=request.user)``
    """
    return get_object_or_404(model, **extra_filters)


def ajax_success(message=None, **extra):
    payload = {"status": "success"}
    if message is not None:
        payload["message"] = message
    payload.update(extra)
    return JsonResponse(payload)


def ajax_error(message, **extra):
    payload = {"status": "error", "message": message}
    payload.update(extra)
    return JsonResponse(payload)
