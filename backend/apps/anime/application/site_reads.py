from celery import shared_task


@shared_task(name='anime.warm_public_catalog')
def warm_public_catalog():
    from django.conf import settings
    from rest_framework.test import APIRequestFactory
    from apps.anime.presentation.views.anime_views import AnimeViewSet
    host = (getattr(settings, 'SITE_URL', None) or 'http://localhost:8080').split('://')[-1].split('/')[0]
    factory = APIRequestFactory()
    for grouped in (False, True):
        parameters = {'page': 1, 'page_size': 50, 'ordering': '-score'}
        if grouped: parameters['group_franchises'] = 'true'
        response = AnimeViewSet.as_view({'get': 'list'})(factory.get('/api/anime/', parameters, HTTP_HOST=host))
        if response.status_code != 200: raise RuntimeError('Catalog warmup failed')
    return 2
