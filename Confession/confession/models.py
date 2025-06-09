from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

TOXIC_WORDS = [
    'stupid', 'idiot', 'kill', 'die', 'suck', 'shut up', 'shutup', 'ass', 'asshole', 'niger', 'nigger', 'nigga'
]

class Confession(models.Model):
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.CharField(max_length=100)
    is_deleted = models.BooleanField(default=False)
    upvotes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.content[:20]
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.CharField(
        max_length=100,
        default='avatar5.png',
        blank=True
    )
    
    last_avatar_change = models.DateTimeField(null=True, blank=True)
    last_password_change = models.DateTimeField(null=True, blank=True)
    is_admin = models.BooleanField(default=False)

    warning_count = models.IntegerField(default=0)
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(blank=True, null=True)
    ban_expiry = models.DateTimeField(blank=True, null=True)

    dismissed = models.BooleanField(default=False)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    dismissed_by = models.ForeignKey(User, null=True, blank=True, 
    on_delete=models.SET_NULL,
    related_name='dismissed_users')

    def add_warning(self, reason):
        self.warning_count += 1
        if self.warning_count >= 3:
            self.is_banned = True
            self.ban_reason = f"Automatic ban after 3 warnings. Last warning: {reason}"
            self.ban_expiry = timezone.now() + timedelta(days=7)
        self.save()

    def save(self, *args, **kwargs):
        if self.pk:
            old = UserProfile.objects.get(pk=self.pk)
            if old.avatar != self.avatar:
                self.last_avatar_change = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_currently_banned(self):
        if not self .is_banned:
            return False
        if self.ban_expiry and self.ban_expiry > timezone.now():
            return True
        self.is_banned = False
        self.ban_expiry = None
        self.ban_reason = ""
        self.save()
        return False

class AvatarChangeLog(models.Model):
    profile = models.ForeignKey('UserProfile', on_delete=models.CASCADE, null=False)
    old_avatar = models.CharField(max_length=100)
    new_avatar = models.CharField(max_length=100)
    changed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return f"{self.profile.user} changed avatar at {self.changed_at}"
    
class PasswordChangeLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return f"{self.user} changed password at {self.changed_at}"

class UserActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50, choices=[
        ('username_change', 'Username Change'),
        ('password_change', 'Password Change'),
        ('avatar_change', 'Avatar Change'),
        ('theme_change', 'Theme Change')
    ])
    old_value = models.CharField(max_length=255, blank=True)
    new_value = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} at {self.timestamp}"

class SessionIdentity(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    update_at = models.DateTimeField(auto_now=True)
    likes_count = models.IntegerField(default=0)
    saved_count = models.IntegerField(default=0)
    report = GenericRelation('Report', related_query_name='post')
    views = models.PositiveIntegerField(default=0)
    session_key = models.CharField(max_length=40, default='anonymous_default_key')

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            content_lower = self.content.lower()
            toxic_words_found = [word for word in settings.TOXIC_WORDS if word in content_lower]
            
            if toxic_words_found:
                Report.objects.create(
                    content_object=self,
                    reason=f"Automatically flagged for toxic language: {', '.join(toxic_words_found)}"
                )
                if self.user:
                    Notification.objects.create(
                        user=self.user,
                        session_key='system',
                        message="Your post was automatically flagged for containing inappropriate language",
                        notification_type='warning'
                    )

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
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='child_comments', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='comment_images/', null=True, blank=True)
    is_gif = models.BooleanField(default=False)
    report = GenericRelation('Report', related_query_name='comment')

    def __str__(self):
        return self.content
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and any(word in self.content.lower() for word in settings.TOXIC_WORDS):
            Report.objects.create(
                content_object=self,
                reason="Automatically flagged for toxic language"
            )
            if self.user:
                Notification.objects.create(
                    user=self.user,
                    message="Your comment was automatically flagged for review",
                    notification_type='warning'
                )

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
    parent_reply = models.ForeignKey('self', null=True, blank=True, related_name='child_replies', on_delete=models.CASCADE)

    content = models.TextField(blank=False)
    session_key = models.CharField(max_length=40)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    like_count = models.IntegerField(default=0)
    image = models.ImageField(upload_to='reply_images/', null=True, blank=True)
    is_gif = models.BooleanField(default=False)

    def __str__(self):
        return f'Reply by {self.session_key} on {self.comment.post.title}'

class ReplyLike(models.Model):
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reply', 'session_key')

    def __str__(self):
        return f"Like by {self.session_key} on Reply {self.reply.id}"

class Report(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    reason = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Report on {self.content_object} ({'resolved' if self.resolved else 'pending'})"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    session_key = models.CharField(max_length=40)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(
        max_length=20,
        choices=[
            ('report', 'Content Reported'),
            ('deleted', 'Content Deleted'),
            ('warning', 'Warning Issued'),
            ('ban', 'Account Banned'),
            ('post_like', 'Post Liked'),
            ('comment_like', 'Comment Liked'),
            ('reply_like', 'Reply Liked'),
            ('new_comment', 'New Comment'),
            ('new_reply', 'New Reply')
        ],
        default='report'
    )
    post = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, blank=True)
    reply = models.ForeignKey('Reply', on_delete=models.CASCADE, null=True, blank=True)
    from_user = models.ForeignKey(
        User,
        related_name='sent_notifications',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user or self.session_key}: {self.message}"

    @classmethod
    def create_notification(
        cls,
        recipient,
        notification_type,
        from_user=None,
        session_key=None,
        post=None,
        comment=None,
        reply=None,
        message=None
    ):
        user = recipient if isinstance(recipient, User) else None

        if user is not None and from_user == user:
            return None

        if user is None:
            if isinstance(recipient, str):
                session_key = recipient
            else:
                session_key = session_key or ''

        notification = cls(
            user=recipient,
            session_key=session_key or '',
            notification_type=notification_type,
            from_user=from_user,
            post=post,
            comment=comment,
            reply=reply,
            message=message
        )
        notification.save()
        return notification


class Save(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=100)
    saved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Saved: {self.post.title} by {self.session_key}"
