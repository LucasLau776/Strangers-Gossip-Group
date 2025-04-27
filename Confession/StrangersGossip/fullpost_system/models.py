from django.db import models
from django.contrib.auth.models import User

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
    
    def __str__(self):
        return f"{self.post.title} reported by {self.session_key}"

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
    parent = models.ForeignKey('self', null=True, blank=True, related_name='child_comments', on_delete=models.CASCADE)

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
    created_at = models.DateTimeField(auto_now_add=True)
    like_count = models.IntegerField(default=0)

    def __str__(self):
        return f'Reply by {self.session_key} on {self.comment.post.title}'

class ReplyLike(models.Model):
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reply', 'session_key')

    def __str__(self):
        return f'{self.session_key} liked reply {self.reply.id}'

class PostSave(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'session_key')
        
    def __str__(self):
        return f"{self.post.title} saved by {self.session_key}"

class PostReport(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class CommentReport(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    reason = models.TextField(null=False, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    
class ReplyReport(models.Model):
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report on Reply {self.reply.id}"