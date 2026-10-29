from django.http import JsonResponse
from django.urls import path
from config.urls import urlpatterns as production_patterns


def identity(request):
    from django.conf import settings
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute('SELECT DATABASE()')
        database = cursor.fetchone()[0]
    valid = database == 'scalability_lab' and settings.DATABASES['default']['HOST'] == 'lab-mysql'
    return JsonResponse({'identity': 'scalability-disposable-lab' if valid else 'invalid'},
                        status=200 if valid else 503, headers={'Cache-Control': 'no-store'})


urlpatterns = [path('__lab_identity', identity), *production_patterns]
