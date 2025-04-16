from django.db import models
from django.contrib.auth.models import User

class Confession(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Confession {self.id}'

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    confession = models.ForeignKey(Confession, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        unique_together = ('user', 'confession')

    def __str__(self):
        return f'{self.user.username} liked Confession {self.confession.id}'

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    confession = models.ForeignKey(Confession, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} commented on Confession {self.confession.id}'
