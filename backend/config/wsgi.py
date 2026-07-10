# =============================================================================
# wsgi.py
# -----------------------------------------------------------------------------
# Expõe a aplicação Django em modo WSGI.
# É usado por servidores tradicionais de produção quando o backend é publicado através de WSGI.
# Carrega config.settings e entrega o objeto application ao servidor.
# =============================================================================
"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
