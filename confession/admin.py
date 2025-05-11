from django.contrib import admin
from . import models
from .models import UserProfile

admin.site.register(models.Confession)
admin.site.register(models.Comment)
admin.site.register(UserProfile)