"""
ASGI config for ts project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from loginCheck.middleware import TokenAuthMiddleware
from loginCheck.consumers import UserStatusConsumer


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ts.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddleware(
        URLRouter([
            path("ws/status", UserStatusConsumer.as_asgi()),
        ])
    ),
})