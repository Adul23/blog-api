from django.db.models import Model, CASCADE, DateTimeField, ForeignKey, BooleanField
from apps.users.models import CustomUser
from apps.blog.models import Comment


class Notification(Model):
    recipient = ForeignKey(CustomUser, on_delete=CASCADE, related_name='notifications')
    comment = ForeignKey(Comment, on_delete=CASCADE)
    is_read = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.email} — comment {self.comment_id}"
