from pathlib import PurePosixPath
from django.http import FileResponse
from django.db.models import Q
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import NotFound
from config.authentication import SoftJWTAuthentication
from apps.users.infrastructure.models.users import User
from apps.users.infrastructure.profile_storage import profile_storage
from apps.users.application.privacy import can_view_field


@api_view(['GET'])
@authentication_classes([SoftJWTAuthentication, SessionAuthentication])
@permission_classes([AllowAny])
def profile_media(request, name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name or not name.startswith('avatars/'):
        raise NotFound()
    owners = User.objects.filter(Q(avatar=name) | Q(profile_settings__avatar=name)).select_related('privacy_settings')
    if not any(can_view_field(owner, request.user, 'who_can_see_profile_photo') for owner in owners):
        raise NotFound()
    if not profile_storage.exists(name):
        raise NotFound()
    response = FileResponse(profile_storage.open(name, 'rb'))
    response['Cache-Control'] = 'private, no-store'
    response['Vary'] = 'Cookie, Authorization'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
