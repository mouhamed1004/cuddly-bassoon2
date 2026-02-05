from django.urls import re_path
from channels.routing import URLRouter
from blizzgame.routing import websocket_urlpatterns

application = URLRouter(websocket_urlpatterns)