 
from django.apps import AppConfig

class TechniciensConfig(AppConfig):
    name = 'apps.techniciens'

    def ready(self):
        import apps.techniciens.signals  # noqa
 