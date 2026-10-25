class SeoPrivacyHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(('/api/', '/admin/', '/ws/')):
            response['X-Robots-Tag'] = 'noindex,follow'
        if request.path.startswith(('/api/anime/', '/api/seo/')) and request.path.rstrip('/').split('/')[-1] not in {'home', 'calendar', 'status'}:
            response['Cache-Control'] = 'private, no-store'
        return response
