import json
from typing import Any
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone


class CommentsConsumer(AsyncWebsocketConsumer):
    slug: str
    group_name: str

    async def connect(self) -> None:
        url_route: dict[str, Any] = self.scope.get("url_route", {})  # type: ignore[typeddict-item]
        kwargs: dict[str, str] = url_route.get("kwargs", {})
        self.slug = kwargs.get("slug", "")
        self.group_name = f"post_{self.slug}_comments"

        if not self.slug:
            await self.close(code=4000)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code: int) -> None:
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(
        self,
        text_data: str | None = None,
        bytes_data: bytes | None = None,
    ) -> None:
        if text_data is None:
            return

        data: dict[str, Any] = json.loads(text_data)
        user: Any = self.scope.get("user")  # type: ignore[typeddict-item]

        if not user or user.is_anonymous:
            await self.close(code=4001)
            return

        message: dict[str, Any] = {
            "comment_id": data.get("comment_id"),
            "author": {
                "id": user.id,
                "email": user.email,
            },
            "body": data.get("body", ""),
            "created_at": timezone.now().isoformat(),
        }

        await self.channel_layer.group_send(
            self.group_name,
            {"type": "comment_message", "message": message},
        )

    async def comment_message(self, event: dict[str, Any]) -> None:
        await self.send(text_data=json.dumps(event["message"]))
