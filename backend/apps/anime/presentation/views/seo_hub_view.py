from django.http import HttpResponsePermanentRedirect, HttpResponseNotFound


def seo_hub_view(request, **kwargs):
    if '/studio/' in request.path:
        response = HttpResponseNotFound()
    else:
        response = HttpResponsePermanentRedirect(request.path.removeprefix('/api').rstrip('/'))
    response['X-Robots-Tag'] = 'noindex,follow'
    response['Cache-Control'] = 'no-store'
    return response
