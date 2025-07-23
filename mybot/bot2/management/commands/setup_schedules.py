from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
from django.utils import timezone

class Command(BaseCommand):
    help = 'Set up scheduled tasks for the activity bot'

    def handle(self, *args, **options):
        self.stdout.write('Setting up scheduled tasks for activity questions...')
        
        # Clear existing tasks to avoid conflicts
        self.stdout.write('Clearing existing tasks...')
        PeriodicTask.objects.all().delete()
        CrontabSchedule.objects.all().delete()
        IntervalSchedule.objects.all().delete()
        self.stdout.write('Cleared existing tasks and schedules')
        
        # Create interval-based schedule (every 30 minutes)
        interval_schedule = IntervalSchedule.objects.create(
            every=30,
            period=IntervalSchedule.MINUTES,
        )
        
        self.stdout.write('Created 30-minute interval schedule')
        
        # Create the periodic task for activity questions
        activity_task = PeriodicTask.objects.create(
            name='send-activity-questions-every-30-minutes',
            task='bot2.tasks.send_activity_questions',
            interval=interval_schedule,
            enabled=True
        )
        
        self.stdout.write('Created activity questions task (every 30 minutes)')
        
        # Create specific time-based schedules for working hours only (9:00-17:00)
        question_times = [
            (9, 0),   # 9:00 AM
            (9, 30),  # 9:30 AM
            (10, 0),  # 10:00 AM
            (10, 30), # 10:30 AM
            (11, 0),  # 11:00 AM
            (11, 30), # 11:30 AM
            (12, 0),  # 12:00 PM
            (12, 30), # 12:30 PM
            (14, 0),  # 2:00 PM
            (14, 30), # 2:30 PM
            (15, 0),  # 3:00 PM
            (15, 30), # 3:30 PM
            (16, 0),  # 4:00 PM
            (16, 30), # 4:30 PM
            (17, 0),  # 5:00 PM
        ]
        
        for hour, minute in question_times:
            # Create the crontab schedule
            schedule = CrontabSchedule.objects.create(
                hour=hour,
                minute=minute,
                day_of_week='*',
                day_of_month='*',
                month_of_year='*',
                timezone='Asia/Almaty'
            )
            
            self.stdout.write(f'Created schedule for {hour:02d}:{minute:02d}')
            
            # Create the periodic task
            task_name = f'send-activity-question-{hour:02d}-{minute:02d}'
            task = PeriodicTask.objects.create(
                name=task_name,
                task='bot2.tasks.send_activity_questions',
                crontab=schedule,
                enabled=True
            )
            
            self.stdout.write(f'Created task: {task_name}')
        
        # Create daily summary task (at 15:38 PM Kazakhstan time)
        summary_schedule = CrontabSchedule.objects.create(
            hour=17,
            minute=0,
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone='Asia/Almaty'
        )
        
        self.stdout.write('Created daily summary schedule (3:38 PM)')
        
        summary_task = PeriodicTask.objects.create(
            name='send-daily-summary',
            task='bot2.tasks.send_daily_summary',
            crontab=summary_schedule,
            enabled=True
        )
        
        self.stdout.write('Created daily summary task')
        
        # Create cleanup task (daily at 2:00 AM)
        cleanup_schedule = CrontabSchedule.objects.create(
            hour=2,
            minute=0,
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone='Asia/Almaty'
        )
        
        self.stdout.write('Created cleanup schedule (2:00 AM)')
        
        cleanup_task = PeriodicTask.objects.create(
            name='cleanup-old-responses',
            task='bot2.tasks.cleanup_old_responses',
            crontab=cleanup_schedule,
            enabled=True
        )
        
        self.stdout.write('Created cleanup task')
        
        # Create health check task (every hour)
        health_schedule = CrontabSchedule.objects.create(
            hour='*',
            minute=0,
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone='Asia/Almaty'
        )
        
        self.stdout.write('Created health check schedule (every hour)')
        
        health_task = PeriodicTask.objects.create(
            name='health-check',
            task='bot2.tasks.health_check',
            crontab=health_schedule,
            enabled=True
        )
        
        self.stdout.write('Created health check task')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up all scheduled tasks!')
        )
        
        self.stdout.write('\n📋 Scheduled Tasks Summary:')
        self.stdout.write('• Activity questions: Every 30 minutes (9:00-17:00)')
        self.stdout.write('• Daily summary: 6:00 PM daily')
        self.stdout.write('• Cleanup: 2:00 AM daily')
        self.stdout.write('• Health check: Every hour')
        self.stdout.write('\n🚀 Start the bot with: python start_celery.py') 