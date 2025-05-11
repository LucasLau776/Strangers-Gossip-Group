from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Confession(models.Model):
    content = models.TextField()  
    timestamp = models.DateTimeField(auto_now_add=True)  
    user = models.CharField(max_length=100)  
    is_deleted = models.BooleanField(default=False)  
    upvotes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.content[:20]

class Comment(models.Model):
    confession = models.ForeignKey('Confession', on_delete=models.CASCADE)  # 留在哪个 confession 上
    content = models.TextField()
    user = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True,related_name='children',  on_delete=models.CASCADE)
    upvotes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user}: {self.content[:30]}"

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    confession = models.ForeignKey('Confession', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'confession')

class CommentLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE)
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'comment')    

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_post_time = models.DateTimeField(null=True, blank=True)  # 上次发帖时间

    def __str__(self):
        return self.user.username           