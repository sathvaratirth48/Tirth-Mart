from django.apps import AppConfig


class UserappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_modules.userapp"
    label = "userapp"

    def ready(self):
        from . import signals  # noqa: F401  (registers the post_save receiver)
