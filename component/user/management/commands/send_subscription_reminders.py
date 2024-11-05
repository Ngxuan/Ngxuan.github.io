from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from component.user.models import Subscription
from datetime import timedelta

class Command(BaseCommand):
    help = 'Send email reminders one day before subscription expiration'

    def add_arguments(self, parser):
        # Optional argument to run in dry-run mode
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='If provided, will not send emails, just log what would be sent.'
        )

    def handle(self, *args, **kwargs):
        dry_run = kwargs.get('dry_run', False)
        tomorrow = timezone.now().date() + timedelta(days=1)
        expiring_subscriptions = Subscription.objects.filter(subscription_end__date=tomorrow)

        if not expiring_subscriptions.exists():
            self.stdout.write(self.style.WARNING('No subscriptions expiring tomorrow.'))
            return

        for subscription in expiring_subscriptions:
            parent = subscription.parent
            user_email = parent.email
            plan_name = subscription.subscription_plan.plan_name

            # Define plain text message (for fallback)
            message = (
                f"Dear {parent.name},\n\n"
                f"We hope you’re enjoying your journey with Little Scholar! "
                f"This is a friendly reminder that your subscription to the {plan_name} plan will expire tomorrow. "
                f"To ensure uninterrupted access to our resources, please take a moment to renew your subscription.\n\n"
                f"If you have any questions, feel free to reach out to our support team—we’re here to help!\n\n"
                f"Warm regards,\nThe Little Scholar Team"
            )

            # Define HTML message with black text
            html_message = (
                f"<p style='color: black;'>Dear {parent.name},</p>"
                f"<p style='color: black;'>We hope you’re enjoying your journey with Little Scholar! "
                f"This is a friendly reminder that your subscription to the <strong>{plan_name}</strong> plan will expire tomorrow. "
                f"To ensure uninterrupted access to our resources, please take a moment to renew your subscription.</p>"
                f"<p style='color: black;'>If you have any questions, feel free to reach out to our support team—we’re here to help!</p>"
                f"<p style='color: black;'>Warm regards,<br>The Little Scholar Team</p>"
            )

            # Log the email being sent
            if dry_run:
                self.stdout.write(self.style.NOTICE(f'Would send email to {user_email}.'))
                self.stdout.write(self.style.NOTICE(f'Subject: "Friendly Reminder: Subscription Expiring Soon"'))
            else:
                try:
                    send_mail(
                        subject='Friendly Reminder: Subscription Expiring Soon',
                        message=message,  # Plain text message
                        from_email='noreply@littlescholar.com',
                        recipient_list=[user_email],
                        html_message=html_message  # HTML message with black text
                    )
                    self.stdout.write(self.style.SUCCESS(f'Successfully sent email to {user_email}.'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to send email to {user_email}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Finished processing subscription reminders.'))
