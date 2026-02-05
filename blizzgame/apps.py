from django.apps import AppConfig


class BlizzgameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blizzgame'
    
    def ready(self):
        # Importer les signaux pour les activer
        import blizzgame.signals