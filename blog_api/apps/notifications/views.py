import json
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from channels.layers import get_channel_layer

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer


# ---------------------------------------------------------------------------
# HTTP Polling endpoints
# ---------------------------------------------------------------------------
# Polling trade-off:
#   Simplicity: polling is trivial to implement — a standard HTTP endpoint
#   with no persistent connections, special protocols, or infrastructure.
#
#   Downsides: latency (the client only sees new data on the next poll
#   interval), and server load (N clients × M polls/sec = many requests
#   even when nothing has changed).
#
#   Polling is acceptable for low-frequency, non-critical data like
#   notification badge counts where a few seconds of delay is fine.
#   Switch to WebSockets or SSE when you need sub-second latency or
#   when the number of connected clients makes polling expensive.
# ---------------------------------------------------------------------------


class NotificationCountView(APIView):
    """GET /api/notifications/count/ — returns unread notification count."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()
        return Response({"unread_count": count})


class NotificationListView(ListAPIView):
    """GET /api/notifications/ — paginated list of user notifications."""
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
        ).select_related('comment', 'comment__author', 'comment__post')


class MarkAllReadView(APIView):
    """POST /api/notifications/read/ — mark all notifications as read."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)
        return Response({"marked_read": updated})


# ---------------------------------------------------------------------------
# SSE — Post Publication Stream (async view)
# ---------------------------------------------------------------------------

async def sse_stream(request):
    """
    GET /api/posts/stream/

    SSE is a good fit here because:
    - Communication is unidirectional (server → client only).
    - Clients only need to passively receive post-publish notifications.
    - SSE provides built-in reconnection via the browser EventSource API.
    - Simpler than WebSockets — no upgrade handshake, no framing.

    Choose WebSockets instead when:
    - You need bidirectional communication (e.g. chat, live comments).
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
