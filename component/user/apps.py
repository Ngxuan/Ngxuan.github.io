from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler
from django.core.management import call_command

class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'component.user'

    def ready(self):
        # Start the scheduler only once when the application starts
        scheduler = BackgroundScheduler()
        scheduler.add_job(call_command, 'cron', hour=8, minute=00,
                          args=['send_subscription_reminders'])  # Run daily at 8:00 AM
        print("UserConfig is ready")
        scheduler.start()

