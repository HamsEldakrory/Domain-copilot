from django.apps import AppConfig


class InfrastructureConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "infrastructure"

    def ready(self):
        from infrastructure.composition_root import bootstrap
        bootstrap()