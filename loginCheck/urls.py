from django.urls import path
from channels.routing import URLRouter
from .consumers import UserStatusConsumer

websocket_urlpatterns = URLRouter([
    path("ws/friend/status", UserStatusConsumer.as_asgi()),
    # 추가 웹소켓 경로 설정
])