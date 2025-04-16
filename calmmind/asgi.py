"""
ASGI config for calmmind project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.sessions import SessionMiddlewareStack

# Import websocket_urlpatterns lazily
def get_websocket_urlpatterns():
    from chatbot.routing import websocket_urlpatterns
    return websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'calmmind.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
     "websocket": SessionMiddlewareStack(  # Add session middleware here
        AuthMiddlewareStack(
            URLRouter(
                get_websocket_urlpatterns()  # Lazily load WebSocket routes
            )
        )
    ),
})