import asyncio
from django.http import StreamingHttpResponse, Http404
from django.utils.http import content_disposition_header
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .releases import public_manifest, read_manifest, release_dir, schedule_build, TARGETS


class ReleasesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get_authenticators(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return []
        return super().get_authenticators()

    def get(self, request):
        try:
            result = public_manifest()
        except ValueError:
            result = {'status': 'unconfigured', 'artifacts': []}
        response = Response(result)
        response['Cache-Control'] = 'no-store'
        return response

    def post(self, request):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            self.permission_denied(request)
        return Response({'release': schedule_build(force=True)}, status=202)


class DownloadView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request, key, name):
        try:
            folder = release_dir(key)
            manifest = read_manifest(key)
        except ValueError:
            raise Http404
        artifact = next((row for target, row in manifest.get('artifacts', {}).items()
            if target in TARGETS and row.get('status') == 'ready' and row.get('filename') == name
            and name.endswith(TARGETS[target][1])), None)
        path = folder / name
        if not artifact or path.name != name or not path.is_file() or not path.resolve().is_relative_to(folder.resolve()):
            raise Http404
        async def chunks():
            with path.open('rb') as installer:
                while block := await asyncio.to_thread(installer.read, 256 * 1024):
                    yield block
        response = StreamingHttpResponse(chunks(), content_type='application/octet-stream')
        response['Content-Length'] = path.stat().st_size
        response['Content-Disposition'] = content_disposition_header(True, name)
        response['Cache-Control'] = 'public, max-age=31536000, immutable'
        response['X-Content-Type-Options'] = 'nosniff'
        return response
