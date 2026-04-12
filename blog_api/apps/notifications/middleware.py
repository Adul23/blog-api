from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


@database_sync_to_async
def get_user_from_jwt(token_string: str):
    try:
        payload = jwt.decode(token_string, settings.SECRET_KEY, algorithms=["HS256"])
        return User.objects.get(id=payload["user_id"])
    except Exception:
        return AnonymousUser()


class TokenAuthMiddleWare:
    """
    Channels middleware that authenticates WebSocket connections
    using a JWT access token passed as a query parameter:
        ws://…?token=<access_token>

    Rejects unauthenticated connections with close code 4001.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_params = parse_qs(scope["query_string"].decode())
        token_list = query_params.get("token", [])

        if not token_list:
            await send({"type": "websocket.close", "code": 4001})
            return

        user = await get_user_from_jwt(token_list[0])

        if user.is_anonymous:
            await send({"type": "websocket.close", "code": 4001})
            return

        scope["user"] = user
        return await self.app(scope, receive, send)
