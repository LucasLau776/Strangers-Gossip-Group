from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, UserActivityLog, Post, Comment, Reply, PostLike, CommentLike, ReplyLike,Report, Notification, Save, SessionIdentity

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    readonly_fields = ('last_password_change',)
    fieldsets = (
        (None, {'fields': ('avatar', 'theme')}),
        ('Security', {
            'fields': ('last_password_change',),
            'classes': ('collapse',)
        }),
    )

class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'timestamp', 'ip_address')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('timestamp', 'ip_address')

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'date_joined', 'last_login', 'get_avatar', 'get_last_username_change')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    
    def get_avatar(self, obj):
        return obj.userprofile.avatar
    get_avatar.short_description = 'Avatar'
    
    def get_last_username_change(self, obj):
        return obj.userprofile.last_username_change
    get_last_username_change.short_description = 'Last Username Change'

admin.site.register(UserActivityLog, UserActivityLogAdmin)
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar', 'last_password_change')
    search_fields = ('user__username',)

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
