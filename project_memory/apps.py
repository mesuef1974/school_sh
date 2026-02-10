from django.apps import AppConfig

class ProjectMemoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'project_memory'
    verbose_name = "ذاكرة المشروع"

    def ready(self):
        # Import signals so they are connected when the app is ready
        import project_memory.signals