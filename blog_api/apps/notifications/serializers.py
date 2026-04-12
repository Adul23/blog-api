from rest_framework.serializers import ModelSerializer, ReadOnlyField
from apps.notifications.models import Notification


class NotificationSerializer(ModelSerializer):
    comment_author = ReadOnlyField(source='comment.author.email')
    post_title = ReadOnlyField(source='comment.post.title')

    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'comment', 'comment_author',
            'post_title', 'is_read', 'created_at',
        ]
        read_only_fields = fields
