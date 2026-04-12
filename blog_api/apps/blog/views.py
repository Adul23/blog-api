import json
import redis

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from django.core.cache import cache
from django.conf import settings
from django.utils import translation
from django.http import StreamingHttpResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from asyncio import gather
import httpx
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_view, extend_schema

from .models import Post, Category, Comment
from .serializers import PostSerializer, CommentSerializer, CategorySerializer


@extend_schema_view(
    list=extend_schema(
        tags=['Posts'],
        summary="List all published posts",
        description=(
            "Retrieves a list of all published posts. "
            "Cached for 15 minutes per language."
        ),
    ),
    create=extend_schema(
        tags=['Posts'],
        summary="Create a new post",
        description=(
            "Creates a new post. The author is automatically set to the authenticated user. "
            "Triggers SSE event if created as published."
        ),
    ),
    comments=extend_schema(
        tags=['Comments'],
        summary="List or Create Post Comments",
        description=(
            "GET: Returns comments for the specific post.\n"
            "POST: Creates a new comment. Dispatches process_new_comment Celery task."
        ),
    ),
)
class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'posts'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            queryset = queryset.filter(status=Post.Status.PUBLISHED)
        return queryset

    def list(self, request, *args, **kwargs):
        lang = translation.get_language()
        cache_key = f"posts_list_cache_{lang}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data).data
        else:
            serializer = self.get_serializer(queryset, many=True)
            response_data = serializer.data

        cache.set(cache_key, response_data, timeout=900)
        return Response(response_data)

    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user)

        # If post is created as published, fire SSE event directly (lightweight)
        if post.status == Post.Status.PUBLISHED:
            _publish_sse_event(post)

    def perform_update(self, serializer):
        old_status = serializer.instance.status
        post = serializer.save()

        # If post transitioned from draft/scheduled to published, fire SSE
        if old_status != Post.Status.PUBLISHED and post.status == Post.Status.PUBLISHED:
            _publish_sse_event(post)

    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def comments(self, request, slug=None):
        post = self.get_object()

        if request.method == 'GET':
            comments = post.comments.all()
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)

        # POST — create comment and dispatch Celery task for side effects
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(author=request.user, post=post)

            # Dispatch Celery task for: Notification creation + WebSocket broadcast
            from apps.notifications.tasks import process_new_comment
            process_new_comment.delay(comment.id)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# ---------------------------------------------------------------------------
# SSE — Post Publication Stream
# ---------------------------------------------------------------------------

async def sse_stream(request):
    """
    GET /api/posts/stream/

    SSE is a good fit here because:
    - Communication is unidirectional (server → client only).
    - Clients only need to passively receive post-publish notifications.
    - SSE provides built-in reconnection via the browser EventSource API.
    - It is simpler to implement and consumes fewer resources than WebSockets.

    Choose WebSockets instead when:
    - You need bidirectional communication (e.g. chat, live collaborative editing).
    - Clients need to send data back to the server in real time.
    """
    async def event_generator():
        channel_layer = get_channel_layer()
        channel_name = await channel_layer.new_channel()
        await channel_layer.group_add("published_posts", channel_name)
        try:
            while True:
                message = await channel_layer.receive(channel_name)
                if message.get("type") == "sse.event":
                    yield f"data: {json.dumps(message['data'])}\n\n"
        finally:
            await channel_layer.group_discard("published_posts", channel_name)

    response = StreamingHttpResponse(
        event_generator(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


# ---------------------------------------------------------------------------
# Stats (async, from hw2)
# ---------------------------------------------------------------------------

User = get_user_model()


class StatsView(APIView):
    permission_classes = []

    @extend_schema(
        tags=['Stats'],
        summary='Get global blog and external API stats',
    )
    async def get(self, request):
        async with httpx.AsyncClient() as client:
            rates_task = client.get("https://open.er-api.com/v6/latest/USD")
            time_task = client.get("https://timeapi.io/api/time/current/zone?timeZone=Asia/Almaty")
            rates_res, time_res = await gather(rates_task, time_task)

        rates_data = rates_res.json()
        time_data = time_res.json()
        total_posts = await Post.objects.acount()
        total_comments = await Comment.objects.acount()
        total_users = await User.objects.acount()

        return Response({
            "blog": {
                "total_posts": total_posts,
                "total_comments": total_comments,
                "total_users": total_users,
            },
            "exchange_rates": {
                "KZT": rates_data.get("rates", {}).get("KZT"),
                "RUB": rates_data.get("rates", {}).get("RUB"),
                "EUR": rates_data.get("rates", {}).get("EUR"),
            },
            "current_time": time_data.get("dateTime"),
        })


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _publish_sse_event(post):
    """Publish an SSE event to the published_posts group via channel layer."""
    from django.utils import timezone

    channel_layer = get_channel_layer()
    event_data = {
        "post_id": post.id,
        "title": post.title,
        "slug": post.slug,
        "author": {
            "id": post.author.id,
            "email": post.author.email,
        },
        "published_at": timezone.now().isoformat(),
    }
    async_to_sync(channel_layer.group_send)(
        "published_posts",
        {"type": "sse.event", "data": event_data},
    )
