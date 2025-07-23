import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot1.settings')

app = Celery('bot1')

# Use Django settings, with CELERY prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically discover tasks from installed apps
app.autodiscover_tasks()

# Set timezone for Celery
app.conf.timezone = 'Asia/Almaty'
"""
# Define periodic task schedule
app.conf.beat_schedule = {
    
    # Every day at 17:30: send daily summary
    'send-daily-summary-every-evening': {
        'task': 'bot2.tasks.send_daily_summary',
        'schedule': crontab(hour=14, minute=35),
    },
    # Daily cleanup of old responses at 00:00
    'cleanup-old-responses-daily': {
        'task': 'bot2.tasks.cleanup_old_responses',
        'schedule': crontab(hour=0, minute=0),
    },
}
"""
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
