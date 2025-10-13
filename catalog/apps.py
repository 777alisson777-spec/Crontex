from django.apps import AppConfig

class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalog"

    def ready(self):
        # registra validações de EAN em variantes
        import catalog.signals.ean  # noqa: F401