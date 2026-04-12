import json
import logging
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def process_new_comment(self, comment_id: int):
    """
    Celery task dispatched when a new comment is created.
    Handles all side effects:
      1. Creates a Notification record for the post author.
      2. Broadcasts the comment via WebSocket to the post's channel group.

    Automatic retries are important here because:
    - The database might be temporarily unavailable (Notification creation).
    - Redis / channel layer might be down (WebSocket broadcast).
    Without retries, the user would silently miss the notification.
    """
    from apps.blog.models import Comment
    from apps.notifications.models import Notification

    comment = Comment.objects.select_related('post', 'post__author', 'author').get(id=comment_id)
    post = comment.post

    if comment.author_id != post.author_id:
        Notification.objects.create(
            recipient=post.author,
            comment=comment,
        )
        logger.info(
            "Notification created for user %s (comment %d on post '%s').",
            post.author.email, comment.id, post.title,
        )

    channel_layer = get_channel_layer()
    message = {
        "comment_id": comment.id,
        "author": {
            "id": comment.author.id,
            "email": comment.author.email,
        },
        "body": comment.body,
        "created_at": comment.created_at.isoformat(),
    }
    async_to_sync(channel_layer.group_send)(
        f"post_{post.slug}_comments",
        {"type": "comment_message", "message": message},
    )
    logger.info("WebSocket broadcast sent for comment %d.", comment.id)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def clear_expired_notifications(self):
    """
    Celery Beat task (daily at 03:00).
    Deletes notifications older than 30 days.

    Automatic retries matter because a transient DB connection issue
    at 3 AM should not leave stale notifications forever.
    """
    from django.utils import timezone
    from datetime import timedelta
    from apps.notifications.models import Notification

    cutoff = timezone.now() - timedelta(days=30)
    deleted_count, _ = Notification.objects.filter(created_at__lt=cutoff).delete()
    logger.info("Cleared %d expired notifications (older than 30 days).", deleted_count)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def generate_daily_stats(self):
    """
    Celery Beat task (daily at 00:00).
    Logs the number of new posts, comments, and users created in the last 24h.

    Retries are important because this task reads from the database,
    which may be briefly unavailable during maintenance windows.
    """
    from django.utils import timezone
    from datetime import timedelta
    from apps.blog.models import Post, Comment
    from django.contrib.auth import get_user_model

    User = get_user_model()
    since = timezone.now() - timedelta(hours=24)

    new_posts = Post.objects.filter(created_at__gte=since).count()
    new_comments = Comment.objects.filter(created_at__gte=since).count()
    new_users = User.objects.filter(date_joined__gte=since).count()

    logger.info(
        "Daily stats — New posts: %d | New comments: %d | New users: %d",
        new_posts, new_comments, new_users,
    )
