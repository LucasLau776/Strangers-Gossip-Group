from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import (
    UserProfile, AvatarChangeLog, UserActivityLog,
    Post, Comment, Reply,
    PostLike, CommentLike, ReplyLike,
    Report, Notification, Save, SessionIdentity
)

# ========== 用户扩展配置 ==========
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    fk_name = 'user'
    can_delete = False
    readonly_fields = ('last_password_change',)
    fieldsets = (
        (None, {'fields': ('avatar', 'theme', 'is_admin')}),
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

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserActivityLog, UserActivityLogAdmin)

# ========== UserProfile 管理 ==========
class AvatarChangeInline(admin.TabularInline):
    model = AvatarChangeLog
    extra = 0
    readonly_fields = ('changed_at', 'ip_address')
    fields = ('old_avatar', 'new_avatar', 'changed_at', 'ip_address')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    inlines = [AvatarChangeInline]
    list_display = ('user', 'avatar_preview', 'get_last_avatar_change', 'last_password_change', 'is_admin')
    list_editable = ('is_admin',)
    search_fields = ('user__username',)

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 50px; height:50px;" />',
                obj.avatar.url if hasattr(obj.avatar, 'url') else obj.avatar
            )
        return "-"
    avatar_preview.short_description = 'Avatar Preview'

    def get_last_avatar_change(self, obj):
        return obj.last_avatar_change.strftime("%Y-%m-%d %H:%M") if obj.last_avatar_change else "Never modified"
    get_last_avatar_change.short_description = 'Last avatar modification time'

@admin.register(AvatarChangeLog)
class AvatarChangeLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'old_avatar', 'new_avatar', 'changed_at', 'ip_address')
    search_fields = ('user__username', 'old_avatar', 'new_avatar')
    list_filter = ('changed_at',)
    readonly_fields = ('changed_at', 'ip_address')

# ========== Post, Comment, Reply 相关 ==========
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
