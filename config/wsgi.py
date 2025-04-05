"""
WSGI config.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import socks
import socket

from django.core.wsgi import get_wsgi_application
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

if settings.PROXY_ENABLE:
    s = socks.socksocket()
    socks.set_default_proxy(socks.SOCKS5, settings.PROXY_HOST, settings.PROXY_PORT)
    socket.socket = socks.socksocket

application = get_wsgi_application()
