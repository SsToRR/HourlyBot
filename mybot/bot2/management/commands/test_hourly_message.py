from django.core.management.base import BaseCommand
from bot2.tasks import send_hourly_question

class Command(BaseCommand):
    help = 'Test the hourly messaging functionality'

    def handle(self, *args, **options):
        self.stdout.write("Testing hourly messaging...")
        
        try:
            result = send_hourly_question()
            if result:
                self.stdout.write(
                    self.style.SUCCESS('Successfully sent hourly messages!')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to send hourly messages.')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            ) 