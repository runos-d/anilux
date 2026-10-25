from django.http import JsonResponse


def disabled_feature(request, *args, **kwargs):
    return JsonResponse({"detail": "Not found."}, status=404)
