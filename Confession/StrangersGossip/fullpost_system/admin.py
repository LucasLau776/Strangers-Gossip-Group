from django.contrib import admin
from .models import SessionIdentity, Post, Comment, PostLike, CommentLike, Reply, ReplyLike, PostSave, PostReport, CommentReport, ReplyReport

class SessionIdentityAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_key')
    search_fields = ('user__username', 'session_key')
    ordering = ('-user',)

class PostAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'created_at','update_at', 'likes_count', 'get_saves_count','views')
    search_fields = ('title', 'content')
    list_filter = ('created_at','update_at',)
    ordering = ('-created_at',)

    def likes_count(self, obj):
        return obj.postlike_set.count()
    likes_count.short_description = 'Likes'

    def get_saves_count(self, obj):
      if obj.pk:
          return obj.postsave_set.count()
      return 0

class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'session_key', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('session_key', 'post__title')
    ordering = ('-created_at',) 
    
class ReplyInline(admin.TabularInline):
    model = Reply
    fields = ('content', 'session_key')
    readonly_fields = ('created_at',)
    
class CommentAdmin(admin.ModelAdmin):
    list_display = ('content', 'created_at', 'updated_at', 'like_count', 'parent')
    list_filter = ('created_at',)
    search_fields = ('session_key', 'content')
    ordering = ('-created_at',)
    inlines = [ReplyInline]

    def like_count(self, obj):
        return obj.likes.count()
    like_count.short_description = 'Like Count' 
    
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'comment', 'session_key', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('session_key', 'comment__content')
    ordering = ('-created_at',)

class ReplyAdmin(admin.ModelAdmin):
    list_display = ('comment', 'content', 'session_key', 'like_count')  

class ReplyLikeAdmin(admin.ModelAdmin):
    list_display = ('reply', 'session_key', 'created_at') 
    
class PostSaveAdmin(admin.ModelAdmin):
    list_display = ('post', 'session_key', 'created_at')
    list_filter = ('created_at',)
    ordering = ('-created_at',)

class PostReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'session_key', 'reason', 'created_at']
    
class CommentReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'comment', 'reporter_session_key', 'reason', 'created_at']
    
class ReplyReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'reply', 'reporter_session_key', 'reason', 'created_at']

# Register models with the custom admin views
admin.site.register(SessionIdentity, SessionIdentityAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(PostLike, PostLikeAdmin)
admin.site.register(CommentLike, CommentLikeAdmin)
admin.site.register(Reply, ReplyAdmin)
admin.site.register(ReplyLike, ReplyLikeAdmin)
admin.site.register(PostSave, PostSaveAdmin)
admin.site.register(PostReport, PostReportAdmin)
admin.site.register(CommentReport, CommentReportAdmin)
admin.site.register(ReplyReport, ReplyReportAdmin)
