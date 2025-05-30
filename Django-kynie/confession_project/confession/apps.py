from django.apps import AppConfig

class ConfessionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'confession'

    def ready(self):
        import confession.signals  # 👈 确保加载 signal
