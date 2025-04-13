from django.db import models

class Confession(models.Model):
    content = models.TextField()  
    timestamp = models.DateTimeField(auto_now_add=True)  
    user = models.CharField(max_length=100)  
    is_deleted = models.BooleanField(default=False)  

    def __str__(self):
        return self.content[:20]  
