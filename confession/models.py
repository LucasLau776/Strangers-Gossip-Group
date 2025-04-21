from django.db import models

class Confession(models.Model):
    content = models.TextField()  
    timestamp = models.DateTimeField(auto_now_add=True)  
    user = models.CharField(max_length=100)  
    is_deleted = models.BooleanField(default=False)  

    def __str__(self):
        return self.content[:20]

class Comment(models.Model):
    confession = models.ForeignKey('Confession', on_delete=models.CASCADE)  # 留在哪个 confession 上
    content = models.TextField()
    user = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user}: {self.content[:30]}"
