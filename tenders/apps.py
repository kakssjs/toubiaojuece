from django.apps import AppConfig
from django.conf import settings


class TendersConfig(AppConfig):
    name = 'tenders'

    def ready(self):
        # SimpleUI removes Django's clickjacking middleware during startup.
        middleware = 'django.middleware.clickjacking.XFrameOptionsMiddleware'
        if middleware not in settings.MIDDLEWARE:
            settings.MIDDLEWARE.append(middleware)
