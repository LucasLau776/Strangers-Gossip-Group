from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Confession(models.Model):
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.CharField(max_length=100)
    is_deleted = models.BooleanField(default=False)
    upvotes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.content[:20]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

class SessionIdentity(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} -> {self.session_key}"

class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    likes_count = models.IntegerField(default=0)
    saved_count = models.IntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    session_key = models.CharField(max_length=40, default='anonymous_default_key')

    def __str__(self):
        return self.title

class PostLike(models.Model):
    post = models.ForeignKey(Post, related_name='likes', on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'session_key')

    def __str__(self):
        return f'{self.session_key} liked {self.post}'

class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    like_count = models.IntegerField(default=0)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='child_comments', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='comment_images/', null=True, blank=True)
    is_gif = models.BooleanField(default=False)

    def __str__(self):
        return self.content

class CommentLike(models.Model):
    comment = models.ForeignKey(Comment, related_name='likes', on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'session_key')

    def __str__(self):
        return f"Like by {self.session_key} on Comment {self.comment.id}"

class Reply(models.Model):
    comment = models.ForeignKey(Comment, related_name='replies', on_delete=models.CASCADE)
    content = models.TextField(blank=False)
    session_key = models.CharField(max_length=40)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)  # ✅ 加这一行
    created_at = models.DateTimeField(auto_now_add=True)
    like_count = models.IntegerField(default=0)
    image = models.ImageField(upload_to='reply_images/', null=True, blank=True)
    is_gif = models.BooleanField(default=False)

    def __str__(self):
        return f'Reply by {self.session_key} on {self.comment.post.title}'

class ReplyLike(models.Model):
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reply', 'session_key')

    def __str__(self):
        return f"Like by {self.session_key} on Reply {self.reply.id}"

class Report(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    reason = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class Notification(models.Model):
    session_key = models.CharField(max_length=40)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"To {self.session_key}: {self.message}"

class Save(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=100)
    saved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Saved: {self.post.title} by {self.session_key}"
