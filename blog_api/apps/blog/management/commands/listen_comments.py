import redis
import json
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Listens for real-time comment events via Redis'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Redis listener... Waiting for comments..."))
        r = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        
        p = r.pubsub()
        
        p.subscribe('comments')
        
        for message in p.listen():
            if message['type'] == 'message':
                raw_data = message['data'].decode('utf-8')
                
                try:
                    event = json.loads(raw_data)
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                    
                    self.stdout.write(f"[{timestamp}] New Comment on '{event.get('post_slug')}':")
                    self.stdout.write(f"   User: {event.get('author')}")
                    self.stdout.write(f"   Body: {event.get('body')}")
                    self.stdout.write("-" * 30)
                except json.JSONDecodeError:
                    self.stdout.write(f"Raw data: {raw_data}")