import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.env.local')

app = Celery('blog_api')

# Read config from Django settings, all Celery-related keys prefixed with CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks.py in all installed apps
app.autodiscover_tasks()

# ---------------------------------------------------------------------------
# Celery Beat schedule
# ---------------------------------------------------------------------------
app.conf.beat_schedule = {
    # Every 1 minute: publish posts with status=scheduled and publish_at <= now()
    'publish-scheduled-posts': {
        'task': 'apps.blog.tasks.publish_scheduled_posts',
        'schedule': 60.0,  # every 60 seconds
    },
    # Daily at 03:00: delete notifications older than 30 days
    'clear-expired-notifications': {
        'task': 'apps.notifications.tasks.clear_expired_notifications',
        'schedule': crontab(hour=3, minute=0),
    },
    # Daily at 00:00: log stats for the last 24 hours
    'generate-daily-stats': {
        'task': 'apps.notifications.tasks.generate_daily_stats',
        'schedule': crontab(hour=0, minute=0),
    },
}
