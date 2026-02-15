from rest_framework.serializers import ModelSerializer, ReadOnlyField
from .models import Post, Category, Tag, Comment

class PostSerializer(ModelSerializer):
    # Display the author's email instead of just the ID (optional)
    author = ReadOnlyField(source='author.email')
    class Meta:
        model = Post
        fields = ['id', 'author', 'title', 'slug', 'body', 'category', 'tags', 'status', 'created_at']
    
class CommentSerializer(ModelSerializer):
    author = ReadOnlyField(source='author.email')
    class Meta:
        model = Comment
        fields = ['id', 'author', 'body', 'created_at']

class CategorySerializer(ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']