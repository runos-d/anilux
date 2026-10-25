from django.urls import re_path
from . import consumers
from .conversation_consumer import ConversationConsumer

websocket_urlpatterns = [
    re_path(r'ws/global/$', consumers.GlobalEventsConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<chat_id>\d+)/$', ConversationConsumer.as_asgi()),
    re_path(r'ws/typing/(?P<chat_id>\d+)/$', ConversationConsumer.as_asgi()),
]
