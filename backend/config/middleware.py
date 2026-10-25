from django.utils import timezone
from django.contrib.sessions.models import Session
from django.http import HttpResponseNotFound
from django.utils.cache import patch_vary_headers
from apps.users.infrastructure.models.users import UserSession
import logging
import secrets

logger = logging.getLogger(__name__)


class ReleaseFeatureGateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from config import feature_flags

        path = request.path_info.rstrip("/").lower()
        disabled = (
            (path.startswith("/api/dubs") and not feature_flags.FEATURE_DUBS_ENABLED)
            or (path.startswith("/api/reactor") and not feature_flags.FEATURE_REACTOR_ENABLED)
            or (path.startswith("/api/users/2fa") and not feature_flags.FEATURE_TWO_FACTOR_ENABLED)
            or (path == "/api/studios/sync" and not feature_flags.FEATURE_STUDIO_SYNC_ENABLED)
            or (
                path.startswith("/api/studios/")
                and "/discussions/" in path
                and path.endswith(("/like", "/dislike"))
                and not feature_flags.FEATURE_STUDIO_REACTIONS_ENABLED
            )
        )
        if disabled:
            return HttpResponseNotFound()
        return self.get_response(request)


class SecurityResponseHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.csp_nonce = secrets.token_urlsafe(18)
        response = self.get_response(request)
        response.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=()",
        )
        response.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.setdefault("X-Content-Type-Options", "nosniff")
        response.setdefault("X-Frame-Options", "DENY")
        response.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; base-uri 'self'; object-src 'none'; "
            "frame-ancestors 'none'; img-src 'self' data: blob: https:; "
            "media-src 'self' blob: https:; connect-src 'self' https: wss:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            f"script-src 'self' 'nonce-{request.csp_nonce}'",
        )
        return response

class OnlineStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.path.startswith('/data/') or request.path.startswith('/media/') or request.path.startswith('/static/'):
            response['Cross-Origin-Resource-Policy'] = 'cross-origin'
        
        if request.path.startswith('/api/social/chat-media/'):
            response['Cross-Origin-Resource-Policy'] = 'same-site'
        elif response.get('Content-Type', '').startswith('image/'):
            response['Cross-Origin-Resource-Policy'] = 'cross-origin'

        self.add_cache_headers(request, response)

        return response

    def add_cache_headers(self, request, response):
        path = request.path
        if response.has_header('Cache-Control'):
            return
        if response.status_code >= 400:
            response['Cache-Control'] = 'private, no-store'
            return
        if path.startswith('/api/') and (path.startswith('/api/social/') or
                request.META.get('HTTP_AUTHORIZATION') or
                getattr(getattr(request, 'user', None), 'is_authenticated', False)):
            response['Cache-Control'] = 'private, no-cache, no-store, must-revalidate'
            patch_vary_headers(response, ['Authorization', 'Cookie'])
            return
        
        if path.startswith('/media/') or path.startswith('/data/media/'):
            response['Cache-Control'] = 'public, max-age=2592000, immutable'
            
        elif path.startswith('/static/'):
            response['Cache-Control'] = 'public, max-age=31536000, immutable'
            
        elif path.startswith('/api/') and request.method == 'GET':
            if not (hasattr(request, 'user') and request.user.is_authenticated and 
                   any(p in path for p in ['/users/me', '/notifications', '/chat', '/messages', '/library'])):
                response['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=60'
            else:
                response['Cache-Control'] = 'private, no-cache, no-store, must-revalidate'
                
        elif path.startswith('/api/') and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            response['Cache-Control'] = 'no-store, private'
            
        else:
            response['Cache-Control'] = 'no-store, private'

    def update_user_session(self, request, user):
        session_key = request.session.session_key
        if session_key:
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')

            device_info = 'Unknown Device'
            if 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent:
                device_info = 'Mobile Device'
            elif 'Windows' in user_agent:
                device_info = 'Windows PC'
            elif 'Mac' in user_agent:
                device_info = 'Mac Computer'
            elif 'Linux' in user_agent:
                device_info = 'Linux Computer'
            else:
                device_info = 'Web Browser'

            ip_address = self.get_client_ip(request)
            location = self.get_location_from_ip(ip_address)

            try:
                UserSession.objects.update_or_create(
                    user=user,
                    session_key=session_key,
                    defaults={
                        'device_info': device_info,
                        'ip_address': ip_address,
                        'location': location,
                        'user_agent': user_agent[:200],
                    }
                )
            except Exception:
                pass  

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_location_from_ip(self, ip_address):
        return "Москва, Россия"


class CSRFExemptMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.headers.get("Upgrade", "").lower() == "websocket":
            setattr(request, "_dont_enforce_csrf_checks", True)
        return self.get_response(request)


class AuthDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', None)

        if auth_header:
            logger.info(f"AuthDebugMiddleware - Request: {request.method} {request.path}")

        response = self.get_response(request)

        return response
