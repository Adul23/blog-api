from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.conf import settings
from .models import Post


@receiver([post_save, post_delete], sender=Post)
def invalidate_post_cache(sender, instance, **kwargs):
    """Invalidate language-specific post list caches on any Post change."""
    for lang_code, _ in settings.LANGUAGES:
        cache_key = f"posts_list_cache_{lang_code}"
        cache.delete(cache_key)
