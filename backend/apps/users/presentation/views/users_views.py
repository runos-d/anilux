from pathlib import Path
from django.contrib.auth import login, logout
from django.contrib.auth.models import update_last_login
from django.utils import timezone
from django.http import FileResponse, HttpResponseRedirect
from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, throttle_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core import signing
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import random
import google.auth.transport.requests
import google.oauth2.id_token
import requests
from apps.users.infrastructure.models.users import (
    User,
    UserProfileSettings,
    ActiveSession,
    NotificationSettings,
    PrivacySettings,
    UserTheme,
    ChatBackground,
    UserActivitySummary,
)
import logging
import hashlib

logger = logging.getLogger(__name__)
from apps.users.presentation.serializers.users_serializers import (
    UserSerializer,
    UserSimpleSerializer,
    RegisterSerializer,
    LoginSerializer,
    GoogleAuthSerializer,
    PasswordResetSerializer,
    ProfileUpdateSerializer,
    UserSessionSerializer,
    UserSettingsSerializer,
    NicknameCheckSerializer,
    ActiveSessionSerializer,
    PublicUserSerializer,
)
from core.redis_events import event_publisher
from apps.users.application.token_sessions import issue_refresh, current_session_key, revoke_sessions

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        from apps.users.presentation.serializers.users_serializers import UserSerializer

        data = UserSerializer(user, context={"request": request}).data

        subscription = getattr(user, "subscription", None)
        profile = getattr(user, "profile_settings", None)

        if profile is not None:
            data["birth_date"] = (
                str(profile.birth_date)
                if getattr(profile, "birth_date", None)
                else None
            )
            data["status"] = getattr(profile, "status", "online") or "online"
            data["social_links"] = getattr(profile, "social_links", []) or []
        else:
            data["birth_date"] = None
            data["status"] = "online"
            data["social_links"] = []

        data["cover_image"] = user.cover_image.url if user.cover_image else None
        data["cover_image_url"] = user.cover_image.url if user.cover_image else None

        data["is_premium"] = subscription.is_premium if subscription else False

        if subscription is not None:
            data["subscription"] = {
                "is_active": subscription.is_premium,
                "started_at": subscription.started_at.isoformat() if subscription.started_at else None,
                "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else None,
                "auto_renew": subscription.auto_renew,
            }
        else:
            data["subscription"] = None

        return Response(data)

    def put(self, request):
        return self._update_profile(request)

    def patch(self, request):
        return self._update_profile(request)

    def delete(self, request):
        return Response(
            {"detail": "Используйте подтверждённый POST /api/users/account-deletion/."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def _update_profile(self, request):
        user = request.user
        serializer = ProfileUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        if "nickname" in validated:
            new_nick = validated["nickname"]
            if new_nick and User.objects.filter(nickname=new_nick).exclude(pk=user.pk).exists():
                return Response({"nickname": "Этот nickname уже занят"}, status=status.HTTP_400_BAD_REQUEST)

        for field, value in validated.items():
            setattr(user, field, value)

        profile_fields = {}
        if "birth_date" in request.data:
            profile_fields["birth_date"] = request.data["birth_date"] or None
        if "status" in request.data:
            profile_fields["status"] = request.data["status"]
        if "social_links" in request.data:
            profile_fields["social_links"] = request.data["social_links"]

        if profile_fields:
            profile, _ = UserProfileSettings.objects.get_or_create(user=user)
            for k, v in profile_fields.items():
                if hasattr(profile, k):
                    setattr(profile, k, v)
            profile.save(update_fields=list(profile_fields.keys()))

        user.save()
        from apps.users.presentation.serializers.users_serializers import UserSerializer

        data = UserSerializer(user, context={"request": request}).data
        try:
            p = user.profile_settings
            data["birth_date"] = (
                str(p.birth_date) if getattr(p, "birth_date", None) else None
            )
            data["social_links"] = getattr(p, "social_links", []) or []
            data["status"] = getattr(p, "status", "online") or "online"
        except Exception:
            pass
        return Response(data)


class LoginRateThrottle(SimpleRateThrottle):
    scope = 'login'

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return f"throttle_{self.scope}_{request.user.pk}"
        return self.ip_key(request)

    def ip_key(self, request):
        ident = request.META.get('REMOTE_ADDR')
        if ident is None:
            ident = 'unknown'
        return f"throttle_{self.scope}_{ident}"


class EmailDestinationRateThrottle(SimpleRateThrottle):
    scope = "email"

    def get_cache_key(self, request, view):
        email = str(request.data.get("email", "")).strip().lower()
        if not email:
            return None
        digest = hashlib.sha256(email.encode("utf-8")).hexdigest()
        return f"throttle_{self.scope}_{digest}"


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer
    throttle_classes = [LoginRateThrottle]

    def perform_create(self, serializer):
        user = serializer.save()
        from apps.users.application.email_service import dispatch_transactional_email

        transaction.on_commit(lambda: dispatch_transactional_email(user, "confirmation"))


class LoginView(APIView):
    permission_classes = (AllowAny,)
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data.get("user")
            if user:
                login(request, user)
                user.is_online = True
                user.save()

                refresh = issue_refresh(user, request)
                update_last_login(None, user)

                return Response(
                    {
                        "user": UserSerializer(user, context={"request": request}).data,
                        "tokens": {
                            "refresh": str(refresh),
                            "access": str(refresh.access_token),
                        },
                    }
                )
        else:
            pass

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleAuthView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        from urllib.parse import urlencode
        import secrets

        state = secrets.token_urlsafe(32)
        request.session["google_oauth_state"] = state
        request.session.save()

        from django.core.cache import cache
        cache.set(f"google_oauth_state:{state}", state, timeout=600)

        redirect_uri = f"{settings.SITE_URL.rstrip('/')}/api/users/google/callback/"
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            logger.debug("ERROR: Google OAuth credentials not configured")
            return Response({"error": "Google OAuth �� ��������"}, status=500)

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }

        google_auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        )
        logger.debug(f"DEBUG: Full Google auth URL: {google_auth_url}")
        return Response({"auth_url": google_auth_url})

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if serializer.is_valid():
            try:
                id_token = serializer.validated_data["id_token"]
                idinfo = google.oauth2.id_token.verify_oauth2_token(
                    id_token,
                    google.auth.transport.requests.Request(),
                    settings.GOOGLE_CLIENT_ID,
                )

                google_id = idinfo["sub"]
                if not idinfo.get("email_verified"):
                    return Response({"error": "Google email is not verified"}, status=400)
                email = idinfo["email"].strip().lower()
                name = idinfo.get("name", "")

                user = User.objects.filter(google_id=google_id).first()
                created = False
                if user is None:
                    user = User.objects.filter(email__iexact=email).first()
                if user is None:
                    user = User.objects.create(
                        google_id=google_id,
                        email=email,
                        username=email.split("@")[0]
                        + str(random.randint(1000, 9999)),
                        first_name=name.split(" ")[0] if name else "",
                        last_name=" ".join(name.split(" ")[1:])
                        if name and len(name.split(" ")) > 1
                        else "",
                        email_verified=True,
                    )
                    created = True
                elif not user.google_id:
                    user.google_id = google_id
                    user.email_verified = True
                    user.save(update_fields=["google_id", "email_verified"])

                if not created and user.email != email:
                    user.email = email
                    user.save()

                login(request, user)
                user.is_online = True
                user.save()
                refresh = issue_refresh(user, request)
                update_last_login(None, user)

                return Response(
                    {
                        "user": UserSerializer(user, context={"request": request}).data,
                        "tokens": {
                            "refresh": str(refresh),
                            "access": str(refresh.access_token),
                        },
                    }
                )

            except Exception as e:
                return Response(
                    {"error": "Google authentication failed"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleAuthCallbackView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")
        error = request.GET.get("error")

        if error:
            return Response({"error": f"Google OAuth error: {error}"}, status=400)

        if not code:
            return Response({"error": "No authorization code received"}, status=400)

        if not state:
            return Response(
                {"error": "Missing state parameter"}, status=400
            )

        from django.core.cache import cache
        cached_state = cache.get(f"google_oauth_state:{state}")

        if not cached_state:
            return Response(
                {"error": "Сессия истекла. Пожалуйста, попробуйте войти снова."},
                status=400
            )

        if state != cached_state:
            return Response({"error": "Invalid state parameter"}, status=400)

        cache.delete(f"google_oauth_state:{state}")

        try:
            redirect_uri = f"{settings.SITE_URL.rstrip('/')}/api/users/google/callback/"
            token_data = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }

            token_response = requests.post(
                "https://oauth2.googleapis.com/token", data=token_data, timeout=15
            )
            token_response.raise_for_status()
            token_json = token_response.json()

            access_token = token_json.get("access_token")
            if not access_token:
                return Response({"error": "Failed to obtain access token"}, status=400)

            user_response = requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            user_response.raise_for_status()
            user_info = user_response.json()

            if not user_info.get("verified_email"):
                return Response({"error": "Google email is not verified"}, status=400)

            google_id = user_info["id"]
            email = user_info["email"].strip().lower()
            name = user_info.get("name", "")
            first_name = user_info.get("given_name", "")
            last_name = user_info.get("family_name", "")

            _base_username = email.split("@")[0] + str(random.randint(1000, 9999))
            user = User.objects.filter(google_id=google_id).first()
            created = False
            if user is None:
                user = User.objects.filter(email__iexact=email).first()
            if user is None:
                user = User.objects.create(
                    google_id=google_id,
                    email=email,
                    username=_base_username,
                    nickname=_base_username,
                    display_name=name or _base_username,
                    first_name=first_name,
                    last_name=last_name,
                    email_verified=True,
                )
                created = True
            elif not user.google_id:
                user.google_id = google_id
                user.email_verified = True
                user.save(update_fields=["google_id", "email_verified"])
            if not created:
                needs_save = False
                if user.email != email:
                    user.email = email
                    needs_save = True
                if not user.nickname:
                    user.nickname = user.username
                    needs_save = True
                if not user.display_name:
                    user.display_name = user.username
                    needs_save = True
                user.first_name = first_name
                user.last_name = last_name
                if needs_save:
                    user.save()

            from django.core.cache import cache
            from django.utils.crypto import get_random_string
            from urllib.parse import urlencode

            exchange_code = get_random_string(64)
            cache.set(f"google-exchange:{exchange_code}", user.pk, timeout=120)
            redirect_url = f"{settings.FRONTEND_PUBLIC_URL}/oauth/callback?{urlencode({'code': exchange_code})}"
            return HttpResponseRedirect(redirect_url)

        except Exception:
            return Response(
                {"error": "Google OAuth callback failed"}, status=500
            )


class GoogleAuthExchangeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from django.core.cache import cache

        code = request.data.get("code", "")
        cache_key = f"google-exchange:{code}"
        user_id = cache.get(cache_key) if code else None
        if not user_id:
            return Response({"error": "invalid_or_expired_code"}, status=400)
        cache.delete(cache_key)
        try:
            user = User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist:
            return Response({"error": "invalid_or_expired_code"}, status=400)
        refresh = issue_refresh(user, request)
        update_last_login(None, user)
        return Response({
            "user": UserSerializer(user, context={"request": request}).data,
            "tokens": {"refresh": str(refresh), "access": str(refresh.access_token)},
        })


class EmailVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        if request.user.email and not request.user.email_verified:
            from apps.users.application.email_service import dispatch_transactional_email

            user = request.user
            transaction.on_commit(lambda: dispatch_transactional_email(user, "confirmation"))
        return Response({"message": "Если подтверждение требуется, письмо будет отправлено"})


class EmailConfirmView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        token = request.query_params.get("token", "")
        if not token:
            return Response({"error": "token_required"}, status=400)
        from apps.users.application.email_service import consume_one_time_token

        try:
            user = consume_one_time_token(token, "confirm")
        except (signing.BadSignature, signing.SignatureExpired, User.DoesNotExist):
            return Response({"error": "invalid_or_expired_token"}, status=400)
        if not user.email_verified:
            user.email_verified = True
            user.save(update_fields=["email_verified"])
        return Response({"success": True})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.is_authenticated:
            user.is_online = False
            user.save()
        refresh_value = request.data.get("refresh")
        if refresh_value:
            try:
                RefreshToken(refresh_value).blacklist()
            except Exception:
                pass
        sid = current_session_key(request)
        if sid:
            revoke_sessions(user, only=sid)
        logout(request)
        return Response({"message": "����� ��������"})


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return User.objects.select_related("subscription", "privacy_settings", "profile_settings").all()

    def get_object(self):
        return self.request.user


class UserPublicProfileView(generics.RetrieveAPIView):
    serializer_class = PublicUserSerializer
    permission_classes = (AllowAny,)
    lookup_field = "pk"

    def get_queryset(self):
        return User.objects.select_related("subscription", "privacy_settings", "profile_settings").all()

    def get_object(self):
        pk = self.kwargs.get("pk")
        try:
            return self.get_queryset().get(pk=pk)
        except User.DoesNotExist:
            raise NotFound("Пользователь не найден")


class UserProfileByNicknameView(generics.RetrieveAPIView):
    serializer_class = PublicUserSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return User.objects.select_related("subscription", "privacy_settings", "profile_settings").all()

    def get_object(self):
        nickname = self.kwargs.get("nickname", "").lstrip("@")
        try:
            return self.get_queryset().get(nickname=nickname)
        except User.DoesNotExist:
            try:
                return User.objects.get(username=nickname)
            except User.DoesNotExist:
                raise NotFound(f"Пользователь @{nickname} не найден")


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle, EmailDestinationRateThrottle])
def password_reset(request):
    serializer = PasswordResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"].strip().lower()
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user:
        from apps.users.application.email_service import dispatch_transactional_email

        transaction.on_commit(lambda: dispatch_transactional_email(user, "password_reset"))
    return Response({"message": "Если адрес зарегистрирован, письмо будет отправлено"})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token", "")
        new_password = request.data.get("new_password", "")
        try:
            user = consume_reset_token(token)
            validate_password(new_password, user=user)
        except (signing.BadSignature, signing.SignatureExpired, User.DoesNotExist):
            return Response({"error": "invalid_or_expired_token"}, status=400)
        except DjangoValidationError as exc:
            return Response({"new_password": list(exc.messages)}, status=400)

        user.set_password(new_password)
        user.save(update_fields=["password"])
        revoke_all_refresh_tokens(user)
        from apps.users.application.email_service import dispatch_transactional_email

        transaction.on_commit(lambda: dispatch_transactional_email(user, "password_changed"))
        return Response({"success": True})


def consume_reset_token(token):
    from apps.users.application.email_service import consume_one_time_token

    return consume_one_time_token(token, "reset")


def revoke_all_refresh_tokens(user):
    from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

    revoke_sessions(user)


class ProfileUpdateView(generics.UpdateAPIView):
    serializer_class = ProfileUpdateSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class UserSessionsView(generics.ListAPIView):
    serializer_class = ActiveSessionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return ActiveSession.objects.filter(user=self.request.user)


class UserSessionDetailView(generics.DestroyAPIView):
    serializer_class = ActiveSessionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return ActiveSession.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        if instance.session_key == current_session_key(self.request):
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Используйте выход для текущей сессии")
        revoke_sessions(self.request.user, only=instance.session_key)
        instance.delete()


class UserSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSettingsSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class OnlineStatusView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user_ids = request.query_params.get("user_ids", "")
        if not user_ids:
            return Response(
                {"error": "user_ids required (comma-separated)"}, status=400
            )

        from core.online_status import online_status

        ids_list = [int(x.strip()) for x in user_ids.split(",") if x.strip().isdigit()]

        if len(set(ids_list)) > 200:
            return Response({'error': 'Передайте до 200 ids'}, status=400)
        online_ids = set(online_status.get_users_data(ids_list))
        users = User.objects.filter(pk__in=ids_list).select_related('settings', 'profile_settings')
        visible = {user.pk for user in users if user.pk == request.user.pk or
                   getattr(getattr(user, 'settings', None), 'show_online_status', True) and
                   getattr(getattr(user, 'profile_settings', None), 'show_online_status', True)}
        result = {uid: uid in online_ids and uid in visible for uid in ids_list}

        return Response(result)


class OnlineUsersView(generics.ListAPIView):
    serializer_class = PublicUserSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        from core.online_status import online_status

        raw_ids = request.query_params.get('ids')
        if raw_ids is not None:
            try:
                ids = {int(value) for value in raw_ids.split(',') if value}
                if len(ids) > 200 or any(pk <= 0 for pk in ids):
                    raise ValueError()
            except ValueError:
                return Response({'error': 'Передайте до 200 положительных ids'}, status=400)
            users = User.objects.filter(pk__in=ids).select_related('settings', 'profile_settings')
            online = online_status.get_users_data(ids)
            return Response({'results': [{'id': user.pk, 'is_online': bool(user.pk in online and
                getattr(getattr(user, 'settings', None), 'show_online_status', True) and
                getattr(getattr(user, 'profile_settings', None), 'show_online_status', True))} for user in users]})
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except ValueError:
            return Response({'error': 'Некорректная страница'}, status=400)
        search = request.query_params.get('search', '').strip()
        queryset = User.objects.exclude(pk=request.user.pk).select_related('settings', 'privacy_settings', 'profile_settings')
        if search:
            queryset = queryset.filter(Q(username__icontains=search) | Q(nickname__icontains=search) | Q(display_name__icontains=search))
            candidates = list(queryset.order_by('pk')[(page - 1) * 50:page * 50 + 1])
            online_ids = set(online_status.get_users_data([user.pk for user in candidates]))
            has_more = len(candidates) > 50
            users = [user for user in candidates[:50] if user.pk in online_ids]
        else:
            rows = online_status.get_online_users(limit=51, offset=(page - 1) * 50)
            has_more = len(rows) > 50
            online_ids = {row['user_id'] for row in rows[:50] if row.get('user_id')}
            users = list(queryset.filter(pk__in=online_ids).order_by('-last_login', 'pk'))
        users = [user for user in users if
                 getattr(getattr(user, 'settings', None), 'show_online_status', True) and
                 getattr(getattr(user, 'profile_settings', None), 'show_online_status', True)]
        data = PublicUserSerializer(users, many=True, context={'request': request}).data
        for item in data:
            item['is_online'] = True
        return Response({'results': data, 'count': len(data), 'has_more': has_more, 'next': page + 1 if has_more else None})


class UserSearchView(generics.ListAPIView):
    serializer_class = PublicUserSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = User.objects.exclude(id=self.request.user.id).select_related(
            "settings", "privacy_settings", "profile_settings"
        )
        exact_username = self.request.query_params.get('username', '').strip()
        if exact_username:
            return queryset.filter(username__iexact=exact_username).order_by('pk')[:1]

        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(nickname__icontains=search)
                | Q(display_name__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        if search:
            queryset = queryset.order_by("-is_online", "-last_login")
        else:
            queryset = queryset.order_by("-is_online", "-last_login")

        return queryset[:50]


class NicknameCheckView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        nickname = request.query_params.get("nickname", "")
        if not nickname:
            return Response(
                {"available": False, "error": "������� �� ������"}, status=400
            )
        from apps.users.infrastructure.models.users import User

        occupied = (
            User.objects.filter(nickname=nickname).exclude(pk=request.user.pk).exists()
        )
        return Response({"available": not occupied, "nickname": nickname})

    def post(self, request):
        serializer = NicknameCheckSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"available": True, "message": "Nickname ��������"})
        return Response(
            {
                "available": False,
                "error": serializer.errors["nickname"][0]
                if "nickname" in serializer.errors
                else "������������ nickname",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class RealtimeUpdatesView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response({"detail": "Use the authenticated WebSocket event stream."}, status=410)


from django.contrib.sessions.models import Session
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_out
from apps.users.infrastructure.models.users import (
    UserSettings,
    UserSession,
    UserProfileSettings,
    NotificationSettings,
    PrivacySettings,
    UserActivitySummary,
)


@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    if created:
        UserSettings.objects.create(user=instance)
        UserProfileSettings.objects.create(user=instance)
        NotificationSettings.objects.create(user=instance)
        PrivacySettings.objects.create(user=instance)


@receiver(post_save, sender=Session)
def create_user_session(sender, instance, created, **kwargs):
    if created:
        try:
            session_data = instance.get_decoded()
            user_id = session_data.get("_auth_user_id")
            if user_id:
                user = User.objects.get(id=user_id)
                user_agent = getattr(instance, "user_agent", "Unknown")

                device_info = "Unknown Device"
                if (
                    "Mobile" in user_agent
                    or "Android" in user_agent
                    or "iPhone" in user_agent
                ):
                    device_info = "Mobile Device"
                elif "Windows" in user_agent:
                    device_info = "Windows PC"
                elif "Mac" in user_agent:
                    device_info = "Mac Computer"
                elif "Linux" in user_agent:
                    device_info = "Linux Computer"
                else:
                    device_info = "Web Browser"

                UserSession.objects.get_or_create(
                    user=user,
                    session_key=instance.session_key,
                    defaults={
                        "device_info": device_info,
                        "user_agent": user_agent[:200],
                    },
                )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Session post_delete error: %s", e)
            raise


@receiver(post_delete, sender=Session)
def cleanup_user_sessions(sender, instance, **kwargs):
    UserSession.objects.filter(session_key=instance.session_key).delete()


@receiver(user_logged_out)
def set_user_offline(sender, user, request, **kwargs):
    if user:
        user.is_online = False
        user.save(update_fields=["is_online"])
        from core.redis_events import publish_user_offline

        publish_user_offline(user.id, user.username)


from rest_framework import viewsets
from apps.users.infrastructure.models.users import (
    UserProfileSettings,
    ActiveSession,
    NotificationSettings,
    PrivacySettings,
    UserTheme,
    ChatBackground,
    UserActivitySummary,
)
from apps.users.presentation.serializers.users_serializers import (
    UserProfileSettingsSerializer,
    ActiveSessionSerializer,
    NotificationSettingsSerializer,
    PrivacySettingsSerializer,
    UserThemeSerializer,
    ChatBackgroundSerializer,
    UserActivitySummarySerializer,
)


class UserProfileSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = UserProfileSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProfileSettings.objects.filter(user=self.request.user)

    def get_object(self):
        settings, created = UserProfileSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        premium_fields = ['nickname_color', 'nickname_gradient_start', 'nickname_gradient_end', 'nickname_glow_enabled', 'nickname_glow_color', 'nickname_glow_intensity']
        changed_premium_fields = [f for f in premium_fields if f in request.data]

        if changed_premium_fields:
            if not instance.is_premium:
                return Response(
                    {"error": "Изменение цвета никнейма доступно только для премиум пользователей"},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()


class SessionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        sessions = ActiveSession.objects.filter(user=request.user)
        serializer = ActiveSessionSerializer(sessions, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def terminate(self, request):
        selector = str(request.data.get("session_key") or "")
        if not selector.isdigit() or len(selector) > 19 or int(selector) > 9223372036854775807:
            return Response({"error": "Некорректная сессия"}, status=400)
        session = ActiveSession.objects.filter(user=request.user, pk=selector).first()
        if not session:
            return Response({"error": "Сессия не найдена"}, status=404)
        if session.session_key == current_session_key(request):
            return Response({"error": "Выберите другую сессию"}, status=400)
        revoke_sessions(request.user, only=session.session_key)
        data = {"success": True}
        if request.auth and not request.auth.get('sid'):
            refresh = issue_refresh(request.user, request)
            data['tokens'] = {"refresh": str(refresh), "access": str(refresh.access_token)}
        return Response(data)

    @action(detail=False, methods=["post"])
    def terminate_all_others(self, request):
        count = revoke_sessions(request.user, keep=current_session_key(request))
        data = {"success": True, "terminated_count": count}
        if request.auth and not request.auth.get('sid'):
            refresh = issue_refresh(request.user, request)
            data['tokens'] = {"refresh": str(refresh), "access": str(refresh.access_token)}
        return Response(data)


class NotificationSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return NotificationSettings.objects.filter(user=self.request.user)

    def get_object(self):
        settings, created = NotificationSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings


class PrivacySettingsViewSet(viewsets.GenericViewSet):
    serializer_class = PrivacySettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PrivacySettings.objects.filter(user=self.request.user)

    def get_object(self):
        settings, created = PrivacySettings.objects.get_or_create(
            user=self.request.user
        )
        return settings

    @action(detail=False, methods=["get", "patch"], url_path="me")
    def me(self, request):
        instance = self.get_object()
        if request.method == "GET":
            return Response(self.get_serializer(instance).data)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def check_visibility(self, request):
        target_user_id = request.query_params.get("user_id")

        if not target_user_id:
            return Response({"error": "user_id ����������"}, status=400)

        try:
            target_user = User.objects.get(id=target_user_id)

            from apps.social.infrastructure.models.social import PrivateChat
            from django.db.models import Q

            is_contact = PrivateChat.objects.filter(
                (Q(user1=request.user) & Q(user2=target_user))
                | (Q(user1=target_user) & Q(user2=request.user))
            ).exists()

            try:
                privacy_settings = target_user.privacy_settings
                visibility = {
                    "phone": self.check_field_visibility(
                        "who_can_see_phone", privacy_settings, is_contact
                    ),
                    "email": self.check_field_visibility(
                        "who_can_see_email", privacy_settings, is_contact
                    ),
                    "last_seen": self.check_field_visibility(
                        "who_can_see_last_seen", privacy_settings, is_contact
                    ),
                    "profile_photo": self.check_field_visibility(
                        "who_can_see_profile_photo", privacy_settings, is_contact
                    ),
                    "can_call": self.check_field_visibility(
                        "who_can_call", privacy_settings, is_contact
                    ),
                    "is_blocked": privacy_settings.blocked_users.filter(
                        id=request.user.id
                    ).exists(),
                }
            except Exception:
                visibility = {
                    "phone": True,
                    "email": True,
                    "last_seen": True,
                    "profile_photo": True,
                    "can_call": True,
                    "is_blocked": False,
                }

            return Response(visibility)

        except User.DoesNotExist:
            return Response({"error": "������������ �� ������"}, status=404)

    def check_field_visibility(self, field_name, privacy_settings, is_contact):
        value = getattr(privacy_settings, field_name)

        if value == "everyone":
            return True
        elif value == "contacts":
            return is_contact
        else:
            return False

    @action(detail=False, methods=["get"])
    def blocked_users(self, request):
        try:
            privacy_settings = request.user.privacy_settings
            blocked_users = privacy_settings.blocked_users.all()
        except Exception:
            blocked_users = []

        from apps.users.presentation.serializers.users_serializers import (
            UserSimpleSerializer,
        )

        serializer = UserSimpleSerializer(blocked_users, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def block_user(self, request):
        user_id = request.data.get("user_id")

        if not user_id:
            return Response({"error": "user_id ����������"}, status=400)

        try:
            user_to_block = User.objects.get(id=user_id)

            try:
                privacy_settings = request.user.privacy_settings

                if privacy_settings.blocked_users.filter(id=user_id).exists():
                    return Response(
                        {"error": "������������ ��� ������������"}, status=400
                    )

                privacy_settings.blocked_users.add(user_to_block)
            except Exception:
                from apps.users.infrastructure.models.users import PrivacySettings

                privacy_settings, created = PrivacySettings.objects.get_or_create(
                    user=request.user
                )
                privacy_settings.blocked_users.add(user_to_block)

            pass

            from apps.social.infrastructure.models.social import PrivateChat

            PrivateChat.objects.filter(
                (Q(user1=request.user) & Q(user2=user_to_block))
                | (Q(user1=user_to_block) & Q(user2=request.user))
            ).delete()

            return Response({"success": True})

        except User.DoesNotExist:
            return Response({"error": "������������ �� ������"}, status=404)

    @action(detail=False, methods=["post"])
    def unblock_user(self, request):
        user_id = request.data.get("user_id")

        if not user_id:
            return Response({"error": "user_id ����������"}, status=400)

        try:
            user_to_unblock = User.objects.get(id=user_id)

            try:
                privacy_settings = request.user.privacy_settings

                if not privacy_settings.blocked_users.filter(id=user_id).exists():
                    return Response(
                        {"error": "������������ �� ������������"}, status=400
                    )

                privacy_settings.blocked_users.remove(user_to_unblock)
            except Exception:
                return Response({"error": "������������ �� ������������"}, status=400)

            return Response({"success": True})

        except User.DoesNotExist:
            return Response({"error": "������������ �� ������"}, status=404)


class UserThemeViewSet(viewsets.ModelViewSet):
    serializer_class = UserThemeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserTheme.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatBackgroundViewSet(viewsets.ModelViewSet):
    serializer_class = ChatBackgroundSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatBackground.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.is_staff
            or request.user.is_superuser
        )


class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta
        from apps.notifications.infrastructure.models.notifications import Notification, Complaint

        now = timezone.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)

        recent_users = User.objects.order_by("-date_joined")[:20]
        recent_users_data = []
        for u in recent_users:
            recent_users_data.append(
                {
                    "id": u.id,
                    "username": u.username,
                    "nickname": u.nickname,
                    "email": u.email,
                    "date_joined": u.date_joined.isoformat() if u.date_joined else None,
                    "is_online": u.is_online,
                    "last_login": u.last_login.isoformat() if u.last_login else None,
                }
            )

        online_users = User.objects.filter(is_online=True).exclude(id=request.user.id)
        online_users_data = []
        for u in online_users:
            online_users_data.append(
                {
                    "id": u.id,
                    "username": u.username,
                    "nickname": u.nickname,
                    "is_online": u.is_online,
                    "last_login": u.last_login.isoformat() if u.last_login else None,
                }
            )

        pending_complaints = Complaint.objects.filter(status="pending").count()

        return Response(
            {
                "stats": {
                    "total_users": User.objects.count(),
                    "online_now": online_users.count(),
                    "registered_today": User.objects.filter(
                        date_joined__gte=today
                    ).count(),
                    "registered_this_week": User.objects.filter(
                        date_joined__gte=week_ago
                    ).count(),
                    "pending_complaints": pending_complaints,
                },
                "recent_registrations": recent_users_data,
                "online_users": online_users_data,
            }
        )


class AdminComplaintsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from apps.notifications.infrastructure.models.notifications import Complaint

        status_filter = request.query_params.get("status", "pending")
        qs = Complaint.objects.select_related(
            "complainant", "assigned_to", "content_type"
        ).order_by("-created_at")
        if status_filter != "all":
            qs = qs.filter(status=status_filter)
        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = max(1, min(int(request.query_params.get("page_size", 20)), 50))
        except (TypeError, ValueError):
            page, page_size = 1, 20
        total = qs.count()
        start = (page - 1) * page_size
        qs = qs[start:start + page_size]

        data = []
        for c in qs:
            target_info = None
            target_user = None
            target_preview = None
            target_url = None
            target_title = None
            target_media = []
            assigned_to_info = None
            snapshot = c.target_snapshot or {}
            target_available = False
            complainant_url = f"/profile/@{c.complainant.nickname}" if c.complainant.nickname else f"/profile/{c.complainant.username}"

            try:
                if c.content_object:
                    obj = c.content_object
                    target_available = (
                        not getattr(obj, "is_deleted", False)
                        and (not isinstance(obj, User) or obj.is_active)
                    )
                    if hasattr(obj, "author"):
                        target_user = obj.author
                        target_info = f"Автор: @{obj.author.username}"
                        if c.complaint_type == "reactor_post":
                            target_url = f"/post/{getattr(obj, 'public_id', obj.id)}" if target_available else None
                            target_title = getattr(obj, "title", None)
                            target_preview = getattr(obj, "text", None) or target_title or ""
                        elif c.complaint_type == "comment":
                            post_available = not getattr(obj.post, "is_deleted", False)
                            target_available = target_available and post_available
                            target_url = f"/post/{getattr(obj.post, 'public_id', obj.post.id)}" if target_available else None
                            target_title = getattr(obj, "content", None)
                            target_preview = target_title or ""
                    elif hasattr(obj, "user"):
                        target_user = obj.user
                        target_info = f"Пользователь: @{obj.user.username}"
                        target_url = f"/profile/@{obj.user.nickname}" if obj.user.nickname else f"/profile/{obj.user.username}"
                        target_preview = getattr(obj, "text", None) or getattr(obj, "content", None)
                    elif hasattr(obj, "username"):
                        target_user = obj
                        target_info = f"Пользователь: @{obj.username}"
                        target_url = f"/profile/@{obj.nickname}" if getattr(obj, "nickname", None) else f"/profile/{obj.username}"
                        target_preview = getattr(obj, "display_name", None) or obj.username
            except Exception:
                pass

            target_title = target_title or snapshot.get("title")
            target_preview = target_preview or snapshot.get("text")
            if snapshot.get("media"):
                from apps.social.infrastructure.post_media_urls import media_url
                target_media = [
                    {
                        **item,
                        "url": media_url(item.get("path"), request) if item.get("path") else None,
                    }
                    for item in snapshot["media"]
                ]
            if not target_info and snapshot.get("author_username"):
                noun = "Пользователь" if c.complaint_type == "user" else "Автор"
                target_info = f"{noun}: @{snapshot['author_username']}"
            if not target_user and snapshot.get("author_id"):
                target_user = User.objects.filter(pk=snapshot["author_id"]).first()

            if c.assigned_to:
                assigned_to_info = {
                    "id": c.assigned_to.id,
                    "username": c.assigned_to.username,
                    "nickname": c.assigned_to.nickname,
                }

            data.append(
                {
                    "id": c.id,
                    "complainant": {
                        "id": c.complainant.id,
                        "username": c.complainant.username,
                        "nickname": c.complainant.nickname,
                    },
                    "complainant_url": complainant_url,
                    "target_info": target_info,
                    "target_user": {
                        "id": target_user.id,
                        "username": target_user.username,
                        "nickname": target_user.nickname,
                    }
                    if target_user
                    else None,
                    "target_url": target_url,
                    "target_preview": target_preview,
                    "target_media": target_media,
                    "target_title": target_title,
                    "complaint_type": c.complaint_type,
                    "reason": c.reason,
                    "description": c.description,
                    "status": c.status,
                    "created_at": c.created_at.isoformat(),
                    "updated_at": c.updated_at.isoformat(),
                    "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
                    "assigned_to": assigned_to_info,
                    "resolution": c.resolution or None,
                    "action_taken": c.action_taken or None,
                    "target_available": target_available,
                    "object_id": c.object_id,
                    "content_type_id": c.content_type_id,
                }
            )
        return Response({
            "results": data,
            "count": total,
            "page": page,
            "page_size": page_size,
            "has_next": start + len(data) < total,
        })

    def patch(self, request, complaint_id):
        from apps.notifications.infrastructure.models.notifications import Complaint, Notification
        from apps.social.infrastructure.models.social import Post, PostComment, Report
        from apps.social.application.post_commands import delete_post

        allowed_actions = {"none", "warn_user", "delete_content", "deactivate_user", "delete_user"}
        new_status = request.data.get("status")
        action_taken = request.data.get("action", "none")
        resolution = str(request.data.get("resolution", "")).strip()
        if new_status not in dict(Complaint.STATUS_CHOICES):
            return Response({"error": "Недопустимый статус жалобы"}, status=400)
        if action_taken not in allowed_actions:
            return Response({"error": "Недопустимое действие модерации"}, status=400)
        if new_status != "resolved" and action_taken != "none":
            return Response({"error": "Действие можно применить только при удовлетворении жалобы"}, status=400)
        if new_status in ("resolved", "dismissed") and not resolution:
            return Response({"error": "Укажите итог рассмотрения для пользователя"}, status=400)

        with transaction.atomic():
            try:
                complaint = Complaint.objects.select_for_update().select_related(
                    "complainant", "content_type"
                ).get(id=complaint_id)
            except Complaint.DoesNotExist:
                return Response({"error": "Жалоба не найдена"}, status=404)

            target = complaint.content_object
            snapshot = complaint.target_snapshot or {}
            target_user = None
            if isinstance(target, User):
                target_user = target
            elif target is not None and hasattr(target, "author"):
                target_user = target.author
            elif snapshot.get("author_id"):
                target_user = User.objects.filter(pk=snapshot["author_id"]).first()

            if action_taken == "delete_content":
                if isinstance(target, Post):
                    if not target.is_deleted:
                        delete_post(target.pk, request.user, moderation=True)
                elif isinstance(target, PostComment):
                    if not target.is_deleted:
                        target.is_deleted = True
                        target.deleted_at = timezone.now()
                        target.save(update_fields=["is_deleted", "deleted_at", "updated_at"])
                else:
                    return Response({"error": "Этот тип контента нельзя удалить"}, status=400)
            elif action_taken in ("deactivate_user", "delete_user"):
                if not target_user:
                    return Response({"error": "Пользователь жалобы больше не найден"}, status=400)
                if target_user.pk == request.user.pk or target_user.is_superuser:
                    return Response({"error": "Нельзя заблокировать этого администратора"}, status=400)
                target_user.is_active = False
                target_user.save(update_fields=["is_active"])

            now = timezone.now()
            complaint.status = new_status
            complaint.assigned_to = request.user
            complaint.resolution = resolution
            complaint.action_taken = "deactivate_user" if action_taken == "delete_user" else action_taken
            complaint.resolved_at = now if new_status in ("resolved", "dismissed") else None
            complaint.save(update_fields=[
                "status", "assigned_to", "resolution", "action_taken", "resolved_at", "updated_at"
            ])

            if complaint.source_report_id:
                Report.objects.filter(pk=complaint.source_report_id).update(
                    status="resolved" if new_status == "resolved" else "rejected" if new_status == "dismissed" else "pending",
                    resolved_by=request.user if new_status in ("resolved", "dismissed") else None,
                    resolved_at=now if new_status in ("resolved", "dismissed") else None,
                    moderation_comment=resolution,
                    action_taken=complaint.action_taken,
                )

            if new_status in ("resolved", "dismissed"):
                status_text = "удовлетворена" if new_status == "resolved" else "отклонена"
                Notification.objects.create(
                    user=complaint.complainant, type="system",
                    title=f"Ваша жалоба #{complaint.pk} рассмотрена",
                    content=f"Жалоба {status_text}. Решение: {resolution}",
                    link="/notifications", is_important=True,
                    dedupe_key=f"complaint:{complaint.pk}:result:{new_status}",
                )
                if target_user and action_taken in ("warn_user", "delete_content", "deactivate_user", "delete_user"):
                    target_titles = {
                        "warn_user": "Предупреждение модерации",
                        "delete_content": "Контент удалён модерацией",
                        "deactivate_user": "Аккаунт деактивирован модерацией",
                        "delete_user": "Аккаунт деактивирован модерацией",
                    }
                    Notification.objects.create(
                        user=target_user, type="warning", title=target_titles[action_taken],
                        content=resolution, link=snapshot.get("url", ""), is_important=True,
                        dedupe_key=f"complaint:{complaint.pk}:action:{target_user.pk}",
                    )

        return Response({
            "success": True, "status": complaint.status,
            "action_taken": complaint.action_taken, "resolution": complaint.resolution,
        })


class AdminDeletePostView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, post_id):
        from apps.social.infrastructure.models.social import Post

        try:
            post = Post.objects.get(id=post_id)
            post.delete()
            return Response({"success": True, "message": f"Пост #{post_id} удалён"})
        except Post.DoesNotExist:
            return Response({"error": "Пост не найден"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class HeartbeatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from core.online_status import online_status

        user = request.user
        is_active = request.data.get("is_active", True)

        try:
            online_status.set_online(
                user.id,
                user.username,
                extra_data={"display_name": user.display_name or user.username},
                is_active=bool(is_active),
                require_connection=True,
            )
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
            return Response({"ok": False, "error": "internal"}, status=500)

        return Response({"ok": True, "is_active": is_active})


from apps.users.presentation.views.users_views_library import UserLibraryViewSet
from apps.users.application.views_library import UserWrappedView


class AvatarUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user

        if "avatar" not in request.FILES:
            return Response(
                {"error": "Файл аватара не предоставлен"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        avatar_file = request.FILES["avatar"]

        if avatar_file.size > 5 * 1024 * 1024:
            return Response(
                {"error": "Размер файла не должен превышать 5MB"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if avatar_file.content_type not in allowed_types:
            return Response(
                {"error": "Допустимы только изображения (JPEG, PNG, GIF, WebP)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.avatar:
            user.avatar.delete(save=False)

        user.avatar = avatar_file
        user.save(update_fields=["avatar"])

        return Response(
            {"success": True, "avatar_url": user.avatar.url if user.avatar else None}
        )

    def delete(self, request):
        user = request.user

        if user.avatar:
            user.avatar.delete(save=True)
            return Response({"success": True, "message": "Аватар удалён"})

        return Response({"error": "Аватар не найден"}, status=status.HTTP_404_NOT_FOUND)


class AvatarFromScreenshotView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        image_data = request.data.get("image_data")
        crop_x = float(request.data.get("crop_x", 50))
        crop_y = float(request.data.get("crop_y", 50))
        zoom = float(request.data.get("zoom", 1.0))

        if not image_data:
            return Response(
                {"error": "Данные изображения не предоставлены"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            import base64
            from io import BytesIO
            from PIL import Image
            from django.core.files.base import ContentFile
            from django.utils import timezone

            if "," in image_data:
                _, data = image_data.split(",", 1)
            else:
                data = image_data

            image_bytes = base64.b64decode(data)
            img = Image.open(BytesIO(image_bytes))

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            if zoom != 1.0 or crop_x != 50 or crop_y != 50:
                width, height = img.size
                crop_scale = 1.0 / max(zoom, 1.0)
                crop_w = int(width * crop_scale)
                crop_h = int(height * crop_scale)

                center_x = int(width * crop_x / 100)
                center_y = int(height * crop_y / 100)

                left = max(0, center_x - crop_w // 2)
                top = max(0, center_y - crop_h // 2)
                right = min(width, left + crop_w)
                bottom = min(height, top + crop_h)

                if right - left < crop_w:
                    left = max(0, right - crop_w)
                if bottom - top < crop_h:
                    top = max(0, bottom - crop_h)

                img = img.crop((left, top, right, bottom))

            img.thumbnail((512, 512), Image.LANCZOS)

            output = BytesIO()
            img.save(output, format="JPEG", quality=90)
            output.seek(0)

            filename = f"avatar_{user.id}_{timezone.now().timestamp()}.jpg"
            avatar_file = ContentFile(output.read(), name=filename)

            if user.avatar:
                user.avatar.delete(save=False)

            user.avatar = avatar_file
            user.save(update_fields=["avatar"])

            return Response(
                {"success": True, "avatar_url": user.avatar.url if user.avatar else None}
            )
        except Exception as e:
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {"error": f"Ошибка установки аватара: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CoverFromScreenshotView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        image_data = request.data.get("image_data")
        crop_x = float(request.data.get("crop_x", 50))
        crop_y = float(request.data.get("crop_y", 50))

        if not image_data:
            return Response(
                {"error": "Данные изображения не предоставлены"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            import base64
            from io import BytesIO
            from PIL import Image
            from django.core.files.base import ContentFile
            from django.utils import timezone

            if "," in image_data:
                _, data = image_data.split(",", 1)
            else:
                data = image_data

            image_bytes = base64.b64decode(data)
            img = Image.open(BytesIO(image_bytes))

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            max_w, max_h = 1920, 600
            if img.width > max_w or img.height > max_h:
                img.thumbnail((max_w, max_h), Image.LANCZOS)

            output = BytesIO()
            img.save(output, format="JPEG", quality=92, optimize=True)
            output.seek(0)

            filename = f"cover_{user.id}_{timezone.now().timestamp()}.jpg"
            cover_file = ContentFile(output.read(), name=filename)

            if user.cover_image:
                user.cover_image.delete(save=False)

            user.cover_image = cover_file
            user.cover_position_x = crop_x
            user.cover_position_y = crop_y
            user.save(update_fields=["cover_image", "cover_position_x", "cover_position_y"])

            return Response(
                {
                    "success": True,
                    "cover_image_url": user.cover_image.url if user.cover_image else None,
                    "cover_position_x": user.cover_position_x,
                    "cover_position_y": user.cover_position_y,
                }
            )
        except Exception as e:
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {"error": f"Ошибка установки обложки: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get("current_password") or request.data.get("old_password")
        new_password = request.data.get("new_password")
        if request.data.get("confirm_password", new_password) != new_password:
            return Response({"confirm_password": "Пароли не совпадают"}, status=400)

        if not current_password or not new_password:
            return Response(
                {"error": "Необходимы current_password и new_password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(current_password):
            return Response(
                {"error": "Неверный текущий пароль"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as exc:
            return Response(
                {"new_password": list(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])
        revoke_all_refresh_tokens(user)

        from apps.users.application.email_service import dispatch_transactional_email
        transaction.on_commit(lambda: dispatch_transactional_email(user, "password_changed"))

        refresh = issue_refresh(user, request)
        return Response({"success": True, "message": "Пароль успешно изменён",
            "tokens": {"refresh": str(refresh), "access": str(refresh.access_token)}})


class AccountDeletionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.social.infrastructure.models.social import Message, Post, PostComment
        from apps.playlists.infrastructure.models.playlists import Playlist

        user = request.user
        return Response({
            "mode": "immediate",
            "recoverable": False,
            "counts": {
                "messages": Message.objects.filter(sender=user).count(),
                "posts": Post.objects.filter(author=user).count(),
                "comments": PostComment.objects.filter(author=user).count(),
                "playlists": Playlist.objects.filter(user=user).count(),
            },
        })

    def post(self, request):
        user = request.user
        password = request.data.get("password")

        if request.data.get("final_confirmation") is not True:
            return Response(
                {"final_confirmation": "Требуется явное подтверждение удаления."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not password or not user.check_password(password):
            return Response(
                {"error": "Неверный пароль"}, status=status.HTTP_400_BAD_REQUEST
            )

        two_factor = getattr(user, "two_factor", None)
        if two_factor and two_factor.is_enabled:
            code = str(request.data.get("two_factor_code") or "").strip()
            if not code or not two_factor.verify_code(code):
                return Response(
                    {"two_factor_code": "Неверный код двухфакторной аутентификации."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        from apps.users.application.data_management import delete_user_account

        deleted = delete_user_account(user.pk)
        if not deleted:
            return Response({"error": "Аккаунт уже удалён"}, status=status.HTTP_409_CONFLICT)
        return Response({"success": True, "message": "Аккаунт и связанные данные удалены без возможности восстановления."})


class ChatBackgroundSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"background": None})

    def post(self, request):
        return Response({"success": True})


class StorageUsageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.users.application.storage_service import StorageService
        return Response(StorageService(request.user).get_storage_usage())


class SyncSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.users.infrastructure.models.users import SyncSettings
        instance, _ = SyncSettings.objects.get_or_create(user=request.user)
        from django.forms.models import model_to_dict
        return Response({k: v for k, v in model_to_dict(instance).items() if k not in ('id', 'user')})

    def put(self, request):
        from apps.users.infrastructure.models.users import SyncSettings
        from rest_framework import serializers
        class Preferences(serializers.ModelSerializer):
            class Meta:
                model = SyncSettings
                exclude = ['id', 'user']
                read_only_fields = ['sync_status', 'last_sync_time', 'next_sync_time', 'updated_at']
        instance, _ = SyncSettings.objects.get_or_create(user=request.user)
        serializer = Preferences(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def post(self, request):
        return Response({"detail": "Изменения аккаунта сохраняются автоматически. Отдельная фоновая синхронизация пока недоступна."}, status=409)


class ExportDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.users.application.data_management import expire_exports
        from apps.users.infrastructure.models.users import DataExport

        expire_exports()
        records = DataExport.objects.filter(user=request.user).order_by("-created_at")[:50]
        return Response({"exports": [self._serialize(record) for record in records]})

    def post(self, request):
        from datetime import timedelta
        from apps.users.application.data_management import EXPORT_CATEGORIES, EXPORT_FORMATS, build_user_export
        from apps.users.application.user_data_tasks import build_data_export_task
        from apps.users.infrastructure.models.users import DataExport

        items = request.data.get("items")
        output_format = request.data.get("format", "json")
        if not isinstance(items, list) or not items or any(item not in EXPORT_CATEGORIES for item in items):
            return Response({"items": "Выберите хотя бы одну поддерживаемую категорию."}, status=400)
        if len(items) != len(set(items)):
            return Response({"items": "Категории не должны повторяться."}, status=400)
        if output_format not in EXPORT_FORMATS:
            return Response({"format": "Поддерживаются json, csv и html."}, status=400)

        record = DataExport.objects.create(
            user=request.user,
            items=items,
            format=output_format,
            expires_at=timezone.now() + timedelta(hours=settings.DATA_EXPORT_TTL_HOURS),
        )
        try:
            build_data_export_task.delay(record.pk)
        except Exception:
            build_user_export(record.pk)
        record.refresh_from_db()
        return Response(self._serialize(record), status=status.HTTP_202_ACCEPTED)

    @staticmethod
    def _serialize(record):
        return {
            "id": record.pk,
            "items": record.items,
            "format": record.format,
            "status": record.status,
            "size": int(record.size) if record.size.isdigit() else None,
            "created_at": record.created_at,
            "expires_at": record.expires_at,
            "error_code": record.error_code or None,
            "download_url": f"/api/users/export-data/{record.pk}/download/" if record.status == "ready" else None,
        }


class ExportDataDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, export_id):
        from apps.users.infrastructure.models.users import DataExport
        return DataExport.objects.filter(pk=export_id, user=request.user).first()

    def get(self, request, export_id):
        record = self.get_object(request, export_id)
        if record is None:
            return Response({"detail": "Экспорт не найден."}, status=404)
        return Response(ExportDataView._serialize(record))

    def delete(self, request, export_id):
        from apps.users.application.data_management import delete_export_file

        record = self.get_object(request, export_id)
        if record is None:
            return Response({"detail": "Экспорт не найден."}, status=404)
        if record.status not in ("queued", "processing"):
            return Response({"detail": "Этот экспорт уже нельзя отменить."}, status=409)
        record.status = "canceled"
        record.save(update_fields=["status"])
        delete_export_file(record)
        return Response(ExportDataView._serialize(record))


class ExportDataDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, export_id):
        from apps.users.application.data_management import delete_export_file, safe_export_path
        from apps.users.infrastructure.models.users import DataExport

        record = DataExport.objects.filter(pk=export_id, user=request.user).first()
        if record is None:
            return Response({"detail": "Экспорт не найден."}, status=404)
        if record.expires_at <= timezone.now():
            delete_export_file(record)
            record.status = "expired"
            record.file_path = ""
            record.save(update_fields=["status", "file_path"])
            return Response({"detail": "Срок хранения экспорта истёк."}, status=410)
        path = safe_export_path(record.file_path)
        if record.status != "ready" or path is None or not path.is_file():
            return Response({"detail": "Экспорт ещё не готов."}, status=409)
        response = FileResponse(path.open("rb"), as_attachment=True, filename=f"anilux-export-{record.pk}.zip")
        response["Cache-Control"] = "private, no-store"
        response["Pragma"] = "no-cache"
        response["X-Content-Type-Options"] = "nosniff"
        return response


class ClearCacheView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.users.application.storage_service import StorageService
        items = request.data.get('items', ['cache'])
        allowed = {'cache', 'images', 'videos', 'search', 'thumbnails', 'temp', 'fonts'}
        if not isinstance(items, list) or any(not isinstance(item, str) or item not in allowed for item in items):
            return Response({'detail': 'Можно очищать только временный кэш. Данные аккаунта не удаляются.'}, status=400)
        StorageService(request.user).clear_cache()
        return Response({"success": True, "message": "Кэш очищен"})


class HeadersDebugView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        safe_names = {"HTTP_ACCEPT", "HTTP_ACCEPT_LANGUAGE", "HTTP_ORIGIN", "HTTP_USER_AGENT"}
        headers = {k: v for k, v in request.META.items() if k in safe_names}
        return Response({"headers": headers})


class AuthDebugView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response(
            {
                "user": request.user.username,
                "authenticated": True,
                "is_staff": request.user.is_staff,
                "is_superuser": request.user.is_superuser,
            }
        )


class UserFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        return Response({"posts": []})


class UserStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        from apps.social.application.post_access import readable_posts
        from apps.social.infrastructure.models.social import Post
        try:
            try:
                user = User.objects.get(pk=int(pk))
            except (ValueError, User.DoesNotExist):
                user = User.objects.get(username=str(pk))
        except User.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=404)

        try:
            followers_count = user.followers_count
        except:
            followers_count = 0

        try:
            following_count = user.following_count
        except:
            following_count = 0

        try:
            level = user.level
        except:
            level = 1

        return Response(
            {
                "user_id": user.id,
                "username": user.username,
                "display_name": user.display_name or user.username,
                "posts_count": readable_posts(Post.objects.filter(author=user), request.user).count(),
                "followers_count": followers_count,
                "following_count": following_count,
                "level": level,
            }
        )


class AllSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _response(user):
        from apps.users.infrastructure.models.users import (
            NotificationSettings, PrivacySettings, TwoFactorAuth, UserProfileSettings,
        )
        from apps.users.presentation.serializers.users_serializers import (
            NotificationSettingsSerializer, PrivacySettingsSerializer,
            TwoFactorAuthSerializer, UserProfileSettingsSerializer,
        )

        profile, _ = UserProfileSettings.objects.get_or_create(user=user)
        notifications, _ = NotificationSettings.objects.get_or_create(user=user)
        privacy, _ = PrivacySettings.objects.get_or_create(user=user)
        two_factor, _ = TwoFactorAuth.objects.get_or_create(user=user)
        return {
            "user": {
                "display_name": user.display_name,
                "nickname": user.nickname,
                "avatar": user.avatar.url if user.avatar else None,
                "bio": user.bio,
                "favorite_genres": user.favorite_genres,
                "website": user.website,
                "vk_profile": user.vk_profile,
                "telegram": user.telegram,
                "phone_number": user.phone_number,
                "email": user.email,
                "email_verified": user.email_verified,
                "phone_verified": user.phone_verified,
            },
            "profile_settings": UserProfileSettingsSerializer(profile).data,
            "notification_settings": NotificationSettingsSerializer(notifications).data,
            "privacy_settings": PrivacySettingsSerializer(privacy).data,
            "two_factor_settings": TwoFactorAuthSerializer(two_factor).data,
        }

    def get(self, request):
        return Response(self._response(request.user))

    def put(self, request):
        from apps.users.infrastructure.models.users import (
            NotificationSettings, PrivacySettings, UserProfileSettings,
        )
        from apps.users.presentation.serializers.users_serializers import (
            NotificationSettingsSerializer, PrivacySettingsSerializer,
            ProfileUpdateSerializer, UserProfileSettingsSerializer,
        )

        user = request.user
        serializers_to_save = []
        if "user" in request.data:
            serializers_to_save.append(ProfileUpdateSerializer(user, data=request.data["user"], partial=True))
        if "profile_settings" in request.data:
            instance, _ = UserProfileSettings.objects.get_or_create(user=user)
            serializers_to_save.append(UserProfileSettingsSerializer(instance, data=request.data["profile_settings"], partial=True))
        if "notification_settings" in request.data:
            instance, _ = NotificationSettings.objects.get_or_create(user=user)
            serializers_to_save.append(NotificationSettingsSerializer(instance, data=request.data["notification_settings"], partial=True))
        if "privacy_settings" in request.data:
            instance, _ = PrivacySettings.objects.get_or_create(user=user)
            serializers_to_save.append(PrivacySettingsSerializer(instance, data=request.data["privacy_settings"], partial=True))
        for serializer in serializers_to_save:
            serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            for serializer in serializers_to_save:
                serializer.save()
        user.refresh_from_db()
        return Response(self._response(user))


class UsersListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from core.online_status import online_status
        from django.db.models import Q

        tab = request.query_params.get("tab") or request.query_params.get(
            "status", "all"
        )
        search = request.query_params.get("search", "").strip()

        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = max(1, min(int(request.query_params.get("page_size", 24)), 100))
        except (TypeError, ValueError):
            page, page_size = 1, 24

        online_ids = set(online_status.get_online_ids()) if tab in ('online', 'offline') else set()
        visible_online = Q(id__in=online_ids) & (
            Q(pk=request.user.pk) | (
                (Q(profile_settings__isnull=True) | Q(profile_settings__show_online_status=True)) &
                (Q(settings__isnull=True) | Q(settings__show_online_status=True))
            )
        )
        if tab == "online":
            users_qs = (
                User.objects.filter(visible_online)
                if online_ids
                else User.objects.none()
            )
        elif tab == "offline":
            users_qs = (
                User.objects.exclude(visible_online)
                if online_ids
                else User.objects.all()
            )
        else:
            users_qs = User.objects.all().order_by("-last_login")

        if search:
            users_qs = users_qs.filter(
                Q(username__icontains=search)
                | Q(nickname__icontains=search)
                | Q(display_name__icontains=search)
            )

        users_qs = users_qs.select_related("subscription", "profile_settings", "privacy_settings", "settings")
        total_count = users_qs.count()

        start = (page - 1) * page_size
        end = start + page_size
        users = list(users_qs[start:end])
        online_by_id = online_status.get_users_data([user.pk for user in users])
        online_ids = set(online_by_id)

        from apps.users.application.privacy import prepare_privacy
        prepare_privacy(users, request.user, {"avatar_url", "last_login"})
        default_avatar_dir = Path(settings.MEDIA_ROOT) / "def_avatars"
        default_avatars = (list(default_avatar_dir.glob("*.jpg")) + list(default_avatar_dir.glob("*.jpeg"))) if default_avatar_dir.exists() else []
        result = []
        for user in users:
            is_online = user.id in online_ids
            user_data = online_by_id.get(user.id)
            is_active = user_data.get("is_active", False) if user_data else False

            is_premium = False
            try:
                sub = user.subscription
                is_premium = sub.is_premium
            except Exception:
                pass

            avatar_url = None
            if user.avatar:
                avatar_url = user.avatar.url
            else:
                if default_avatars:
                    selected_avatar = default_avatars[user.id % len(default_avatars)]
                    avatar_url = f"/media/def_avatars/{selected_avatar.name}"

            result.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "nickname": user.nickname or user.username,
                    "display_name": user.display_name or user.username,
                    "avatar_url": avatar_url,
                    "is_online": is_online,
                    "is_active": is_active,
                    "is_premium": is_premium,
                    "level": getattr(user, "level", 1),
                    "bio": getattr(user, "bio", None) or getattr(user.profile_settings, "bio", None) if hasattr(user, "profile_settings") else None,
                    "last_login": user.last_login.isoformat()
                    if user.last_login
                    else None,
                }
            )

        from apps.users.application.privacy import project_user
        result = [project_user(data, user, request.user) for data, user in zip(result, users)]
        return Response(
            {
                "results": result,
                "count": total_count,
                "next": f"/api/users/users/?page={page + 1}&page_size={page_size}&tab={tab}&search={search}" if end < total_count else None,
                "previous": f"/api/users/users/?page={page - 1}&page_size={page_size}&tab={tab}&search={search}" if page > 1 else None,
            }
        )
