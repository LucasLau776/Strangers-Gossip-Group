from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import SessionIdentity
from notification_system.models import Notification
from .models import PostLike, CommentLike, ReplyLike, Comment, Reply
from django.db.models.signals import post_save

@receiver(user_logged_in)
def bind_session_to_user(sender, request, user, **kwargs):
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    SessionIdentity.objects.update_or_create(
        user=user,
        defaults={'session_key': session_key}
    )

# like notification
@receiver(post_save, sender=PostLike)
def create_post_like_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient_key=instance.post.session_key,
            sender_key=instance.session_key,
            notification_type='post_like',
            post=instance.post
        )

@receiver(post_save, sender=CommentLike)
def create_comment_like_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient_key=instance.comment.session_key,
            sender_key=instance.session_key,
            notification_type='comment_like',
            comment=instance.comment,
            post=instance.comment.post
        )
        
# reply notification
@receiver(post_save, sender=Reply)
def create_reply_notification(sender, instance, created, **kwargs):
    if created and instance.comment.session_key != instance.session_key:
        Notification.objects.create(
            recipient_key=instance.comment.session_key,
            sender_key=instance.session_key,
            notification_type='comment_reply',
            comment=instance.comment,
            reply=instance,
            post=instance.comment.post
        )