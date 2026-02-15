import json
import redis
from django.conf import settings

redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

def publish_json_event(json_data, channel_name):
    """Publishes a JSON serializable object to a Redis channel."""
    try:
        # Serialize the JSON data to a string before publishing
        message = json.dumps(json_data)
        redis_client.publish(channel_name, message)
        print(f"Published to channel {channel_name}: {message}")
    except Exception as e:
        print(f"Error publishing to Redis: {e}")
