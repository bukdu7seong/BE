"""
ASGI config for ts project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter
from loginCheck.middleware import TokenAuthMiddleware
import loginCheck.urls as loginCheck_urls

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ts.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddleware(
        loginCheck_urls.websocket_urlpatterns
    ),
})