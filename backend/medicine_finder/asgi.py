import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medicine_finder.settings")

from django.core.asgi import get_asgi_application

application = get_asgi_application()
