# component/achievement/apps.py

from django.apps import AppConfig

print("AchievementConfig module loaded")  # Debugging print to check module load

class AchievementConfig(AppConfig):
    name = 'component.achievement'

    def ready(self):

        import component.achievement.signals
        print("AchievementConfig is ready")
