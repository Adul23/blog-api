import redis
import json
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.throttling import ScopedRateThrottle
from django.core.cache import cache
from django.utils import translation # <-- Added this import
from .models import Post, Category, Comment
from .serializers import PostSerializer, CommentSerializer, CategorySerializer
from django.conf import settings
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiExample
from asyncio import gather
import httpx
from django.contrib.auth import get_user_model
from rest_framework.views import APIView



@extend_schema_view(
    list=extend_schema(
        tags=['Posts'],
        summary="List all published posts",
        description=(
            "Retrieves a list of all published posts. "
            "Dates are converted to the authenticated user's timezone and formatted "
            "according to their language. Anonymous users see UTC. "
            "Side effect: This endpoint relies on language-aware Redis caching. "
            "Cached for 15 minutes."
        )
    ),
    create=extend_schema(
        tags=['Posts'],
        summary="Create a new post",
        description=(
            "Creates a new post. The author is automatically set to the authenticated user. "
            "Side effect: Triggers a signal that invalidates the Posts cache for all supported languages."
        )
    ),
    comments=extend_schema(
        tags=['Comments'],
        summary="List or Create Post Comments",
        description=(
            "GET: Returns comments for the specific post.\n"
            "POST: Creates a new comment. \n"
            "Side effect (POST): Publishes a real-time 'new_comment' event to Redis."
        )
    )
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
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def comments(self, request, slug=None):
        post = self.get_object()
        
        if request.method == 'GET':
            comments = post.comments.all()
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)
        
        if request.method == 'POST':
            serializer = CommentSerializer(data=request.data)
            if serializer.is_valid():
                comment = serializer.save(author=request.user, post=post)
                
                try:
                    r = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
                    event_data = {
                        "event": "new_comment",
                        "post_slug": post.slug,
                        "author": request.user.email,
                        "body": comment.body
                    }
                    r.publish('comments', json.dumps(event_data))
                except Exception as e:
                    print(f"Redis Error: {e}")

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

User = get_user_model()
class StatsView(APIView):
    permission_classes = []
    @extend_schema(
        tags=['Stats'],
        summary='Get global blog and external API stats',
        description=('Fetches total blog counts and asynchonously fethces live exchange rates')
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
                "total_users": total_users
            }, "exchange_rates": {
                "KZT": rates_data.get("rates", {}).get('KZT'),
                "RUB": rates_data.get("rates", {}).get('RUB'),
                "EUR": rates_data.get("rates", {}).get('EUR'),
            }, "current_time": time_data.get("dateTime")
            
        })