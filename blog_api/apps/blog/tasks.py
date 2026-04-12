import json
import logging
from celery import shared_task
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def invalidate_posts_cache(self):
    """
    Invalidate all language-specific post list caches.

    Automatic retries are important here because the cache backend (Redis)
    may be temporarily unavailable due to network issues or restarts.
    Without retries, a failed invalidation would leave stale data in cache
    until the next TTL expiry.
    """
    for lang_code, _ in settings.LANGUAGES:
        cache_key = f"posts_list_cache_{lang_code}"
        cache.delete(cache_key)
    logger.info("Post list caches invalidated for all languages.")


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def publish_scheduled_posts(self):
    """
    Celery Beat task (runs every 1 minute).
    Finds posts with status=scheduled and publish_at <= now(),
    sets them to published, and triggers SSE event for each.
    """
    from apps.blog.models import Post
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    now = timezone.now()
    posts = Post.objects.filter(
        status=Post.Status.SCHEDULED,
        publish_at__lte=now,
    )

    channel_layer = get_channel_layer()
    count = 0

    for post in posts:
        post.status = Post.Status.PUBLISHED
        post.save(update_fields=["status", "updated_at"])

        # Trigger SSE event via channel layer
        event_data = {
            "post_id": post.id,
            "title": post.title,
            "slug": post.slug,
            "author": {
                "id": post.author.id,
                "email": post.author.email,
            },
            "published_at": now.isoformat(),
        }
        async_to_sync(channel_layer.group_send)(
            "published_posts",
            {"type": "sse.event", "data": event_data},
        )
        count += 1

    if count:
        logger.info("Published %d scheduled posts.", count)
