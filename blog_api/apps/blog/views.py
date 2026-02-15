import redis
import json
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.throttling import ScopedRateThrottle
from django.core.cache import cache
from .models import Post, Category
from .serializers import PostSerializer, CommentSerializer, CategorySerializer
from django.conf import settings

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = 'slug' 
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    # Apply throttling to the whole viewset
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'posts' 

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            queryset = queryset.filter(status=Post.Status.PUBLISHED)
        return queryset

    def perform_create(self, serializer):
        # Save author automatically
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