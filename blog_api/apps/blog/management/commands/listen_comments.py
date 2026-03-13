import redis.asyncio as redis
import json
import datetime
from django.core.management.base import BaseCommand
from django import conf
from settings import base
import asyncio 

class Command(BaseCommand):
    help = 'Listens for real-time comment events via Redis'

    def handle(self, *args, **options):
        asyncio.run(self.listen())
    
    async def listen(self):
        """
        Why asyncio? Cause Asyncio a signle thread can efficiently suspend execution while waiting for messages freeing up the event loop 
        to perform other tasks.
        """
        r = redis.from_url(f"redis://{base.REDIS_HOST}: {base.REDIS_PORT}")
        pubsub = r.pubsub()
        await pubsub.subscribe('comments')
        self.stdout.write(self.style.SUCCESS("Async redis listener started on comments channel"))

        try:
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    data = json.loads(message['data'].decode('utf-8'))
                    self.stdout.write(
                        self.style.write(
                            self.style.SUCCESS(f"Comment on {data.get('post_slug')} " f"by Author ID: {data.get("author")}: {data.get("body")}")
                        )
                    )
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe('comments')
            await r.close()