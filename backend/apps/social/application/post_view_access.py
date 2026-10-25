import inspect
from rest_framework.response import Response
from apps.social.application.post_access import readable_posts, resolve_post_id
from apps.social.infrastructure.models.social import Post


def guard_actions(namespace):
    for name, view in list(namespace.items()):
        cls = getattr(view, 'cls', None)
        if not cls or getattr(cls, '_post_access_guarded', False):
            continue
        cls._post_access_guarded = True
        for method in cls.http_method_names:
            original = getattr(cls, method, None)
            if original is None:
                continue
            def handler(self, request, *args, _original=original, _name=name, **kwargs):
                key = 'post_id' if 'post_id' in kwargs else None
                pk = resolve_post_id(kwargs[key]) if key else None
                if key: kwargs[key] = pk
                if pk is not None and not readable_posts(Post.objects.filter(pk=pk), request.user).exists():
                    if _name != 'edit_post':
                        return Response({'detail': 'Пост недоступен'}, status=404)
                return _original(self, request, *args, **kwargs)
            setattr(cls, method, handler)
