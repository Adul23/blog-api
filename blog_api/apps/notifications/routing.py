from django.urls import re_path
from apps.notifications.consumers import CommentsConsumer

websocket_urlpatterns = [
    re_path(r"ws/posts/(?P<slug>[\w-]+)/comments/$", CommentsConsumer.as_asgi()),
]
