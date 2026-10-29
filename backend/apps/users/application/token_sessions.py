"""JWT credentials share the lifetime of the server-side login session."""
from django.contrib.auth import login
from django.contrib.sessions.models import Session
from django.db.models import F, OuterRef, Subquery
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken


def validate_token_session(token, user):
    sid = token.get('sid')
    if sid:
        from apps.users.infrastructure.models.users import ActiveSession
        if not str(sid).isdigit():
            raise AuthenticationFailed('Invalid login session')
        live_session = Session.objects.filter(session_key=OuterRef('session_key'), expire_date__gt=timezone.now())
        encoded = ActiveSession.objects.filter(pk=sid, user=user).annotate(
            live_data=Subquery(live_session.values('session_data')[:1]),
        ).values_list('live_data', flat=True).first()
        data = Session(session_data=encoded).get_decoded() if encoded else {}
        if str(data.get('_auth_user_id')) != str(user.pk) or data.get('_auth_user_hash') != user.get_session_auth_hash():
            raise AuthenticationFailed('Login session was revoked')
    elif token.get('ver', 0) != user.token_version:
        raise AuthenticationFailed('Login session was revoked')


def bind_refresh(refresh, user, request):
    from apps.users.infrastructure.models.users import ActiveSession
    if (not request.session.session_key or str(request.session.get('_auth_user_id')) != str(user.pk)
            or request.session.get('_auth_user_hash') != user.get_session_auth_hash()):
        login(request, user)
    request.session.save()
    session, _ = ActiveSession.objects.update_or_create(user=user, session_key=request.session.session_key, defaults={
        'device_info': {'device': request.META.get('HTTP_USER_AGENT', 'Browser')[:120]},
        'ip_address': request.META.get('REMOTE_ADDR') or '127.0.0.1',
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
    })
    # JWTs and the session list expose an opaque selector, never the Django cookie secret.
    refresh['sid'] = str(session.pk)
    refresh['ver'] = user.token_version
    OutstandingToken.objects.filter(jti=refresh['jti']).update(token=str(refresh))
    return refresh


def issue_refresh(user, request):
    return bind_refresh(RefreshToken.for_user(user), user, request)


def validate_socket_session(scope, user, token=None):
    if token is not None:
        validate_token_session(token, user)
        return
    key = getattr(scope.get('session'), 'session_key', None)
    session = Session.objects.filter(session_key=key, expire_date__gt=timezone.now()).first() if key else None
    data = session.get_decoded() if session else {}
    if str(data.get('_auth_user_id')) != str(user.pk) or data.get('_auth_user_hash') != user.get_session_auth_hash():
        raise AuthenticationFailed('Login session was revoked')


def current_session_key(request):
    from apps.users.infrastructure.models.users import ActiveSession
    sid = request.auth.get('sid') if request.auth and hasattr(request.auth, 'get') else None
    if sid and str(sid).isdigit():
        return ActiveSession.objects.filter(pk=sid, user=request.user).values_list('session_key', flat=True).first()
    return request.session.session_key


def revoke_sessions(user, *, keep=None, only=None):
    from apps.users.infrastructure.models.users import User, UserSession, ActiveSession
    session_keys = dict(ActiveSession.objects.filter(user=user).values_list('pk', 'session_key'))
    keys = [key for key in session_keys.values() if key != keep and (only is None or key == only)]
    legacy_keys = UserSession.objects.filter(user=user).values_list('session_key', flat=True)
    keys = list(set(keys) | {key for key in legacy_keys if key != keep and (only is None or key == only)})
    for outstanding in OutstandingToken.objects.filter(user=user):
        try:
            selector = UntypedToken(outstanding.token).get('sid')
            sid = session_keys.get(int(selector)) if selector and str(selector).isdigit() else None
        except Exception:
            sid = None
        if sid == keep and keep:
            continue
        if only is None or sid == only or not sid:
            BlacklistedToken.objects.get_or_create(token=outstanding)
    # Legacy credentials have no sid and cannot be attributed to one device.
    User.objects.filter(pk=user.pk).update(token_version=F('token_version') + 1)
    user.refresh_from_db(fields=['token_version'])
    Session.objects.filter(session_key__in=keys).delete()
    UserSession.objects.filter(user=user, session_key__in=keys).delete()
    ActiveSession.objects.filter(user=user, session_key__in=keys).delete()
    return len(keys)
