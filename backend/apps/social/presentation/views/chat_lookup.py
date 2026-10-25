from django.db import transaction
from apps.social.application.conversations import resolve_chat


class ChatLookupMixin:
    lookup_url_kwarg = 'pk'

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if self.kwargs.get('pk'):
            chat = resolve_chat(self.kwargs['pk'], request.user, self.chat_kind)
            self.kwargs['pk'] = chat.pk

    @transaction.atomic
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if response.status_code >= 400:
            transaction.set_rollback(True)
        return response
