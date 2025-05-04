from django.db import models
from fullpost_system.models import Post, Comment, Reply

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('post_like', 'Post Liked'),
        ('comment_like', 'Comment Liked'),
        ('reply_like', 'Reply Liked'),
        ('post_comment', 'Post Commented'),
        ('comment_reply', 'Comment Replied'),
    )
    
    recipient_key = models.CharField(max_length=40)
    sender_key = models.CharField(max_length=40, null=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    post = models.ForeignKey(Post, null=True, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, null=True, on_delete=models.CASCADE)
    reply = models.ForeignKey(Reply, null=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient_key', 'is_read']),
        ]

    def get_message(self):
        messages = {
            'post_like': f"??? liked your post: {self.post.title}",
            'comment_like': f"??? liked your comment on '{self.comment.post.title}'",
            'reply_like': f"??? liked your reply to '{self.reply.comment.content[:30]}...'",
            'post_comment': f"??? commented on your post: {self.post.title}",
            'comment_reply': f"??? replied to your comment: '{self.comment.content[:30]}...'"
        }
        return messages.get(self.notification_type, "New activity")