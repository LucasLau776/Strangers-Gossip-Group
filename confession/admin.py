from django.contrib import admin
from .models import (
    Post, Comment, Reply,
    PostLike, CommentLike, ReplyLike,Report, Notification, Save, 
    SessionIdentity
)

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0

class ReplyInline(admin.TabularInline):
    model = Reply
    extra = 0

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at', 'likes_count', 'views')
    inlines = [CommentInline]

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'content', 'created_at', 'like_count')
    inlines = [ReplyInline]

@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'comment', 'content', 'created_at', 'like_count')

@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'session_key')

@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'comment', 'session_key')

@admin.register(ReplyLike)
class ReplyLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'reply', 'session_key')

@admin.register(SessionIdentity)
class SessionIdentityAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_key', 'created_at')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_type', 'object_id', 'reason', 'timestamp')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'session_key', 'message', 'is_read', 'created_at')

@admin.register(Save)
class SaveAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'session_key', 'saved_at')
