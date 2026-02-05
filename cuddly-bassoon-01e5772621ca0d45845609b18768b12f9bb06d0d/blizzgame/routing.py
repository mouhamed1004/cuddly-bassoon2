from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/transaction/(?P<transaction_id>[0-9a-f-]+)/$', consumers.TransactionChatConsumer.as_asgi()),
    re_path(r'ws/chat/dispute/(?P<dispute_id>[0-9a-f-]+)/$', consumers.DisputeChatConsumer.as_asgi()),
]