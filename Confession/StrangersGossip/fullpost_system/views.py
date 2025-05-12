from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import Post, Comment, PostLike, CommentLike, Reply, ReplyLike, PostSave, PostReport, CommentReport, ReplyReport, SessionIdentity, Notification


def get_session_key(request):
    if request.user.is_authenticated:
        identity = SessionIdentity.objects.filter(user=request.user).first()
        if identity:
            return identity.session_key
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def full_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    session_key = get_session_key(request)
    post.views += 1
    post.save()
    
    comments = Comment.objects.filter(post=post).order_by('-created_at')
    comments = post.comments.all().prefetch_related('replies')
    for comment in comments:
        comment.current_session_key = request.session.session_key
        
    session_liked_reply_ids = ReplyLike.objects.filter(
        session_key=session_key,
        reply__comment__post=post
    ).values_list('reply_id', flat=True)

    liked = PostLike.objects.filter(post=post, session_key=session_key).exists()
    saved = PostSave.objects.filter(post=post, session_key=session_key).exists()
    post_like_count = PostLike.objects.filter(post=post).count()
    total_comments = comments.count() + sum(comment.replies.count() for comment in comments)

    return render(request, "full_post.html", {
        'post': post,
        'liked': liked,
        'saved': saved,
        'post_like_count': post_like_count,
        'comments': comments,
        'total_comments': total_comments,
        'session_key': session_key,
        'session_liked_reply_ids': list(session_liked_reply_ids),
    })
    

def done_report(request):
    return render(request, 'done_report.html')


def toggle_save_post(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    session_key = get_session_key(request)
    post = get_object_or_404(Post, id=post_id)
    save_obj = PostSave.objects.filter(post=post, session_key=session_key).first()

    if save_obj:
        save_obj.delete()
        saved = False
    else:
        PostSave.objects.create(post=post, session_key=session_key)
        saved = True
    return JsonResponse({'saved': saved})


def bookmark_view(request):
    session_key = get_session_key(request)
    saved_post_relations = PostSave.objects.filter(session_key=session_key).select_related('post').order_by('-created_at')
    saved_posts = [relation.post for relation in saved_post_relations]
    return render(request, 'bookmark.html', {'saved_posts': saved_posts})


def like_post(request, post_id):
    session_key = get_session_key(request)
    post = get_object_or_404(Post, id=post_id)
    
    like, created = PostLike.objects.get_or_create(
        post=post, 
        session_key=session_key
    )
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        if post.session_key != session_key:
            Notification.objects.create(
                recipient_session_key=post.session_key,
                sender_session_key=session_key,
                notification_type='post_like',
                post=post
            )
    
    like_count = PostLike.objects.filter(post=post).count()
    
    return JsonResponse({
        "liked": liked,
        "like_count": like_count,
        "status": "success"
    })


@csrf_exempt
def report_post(request, post_id):
    if request.method == 'POST':
        reason = request.POST.get('reason')
        session_key = get_session_key(request)
        PostReport.objects.create(post_id=post_id, reason=reason, session_key=session_key)
        return redirect('done_report')
    return render(request, 'report.html', {'post_id': post_id})

def report_view(request, content_type, object_id):
    if request.method == 'POST':
        reason = request.POST.get('reason')
        session_key = get_session_key(request)

        if content_type == 'comment':
            CommentReport.objects.create(
                comment_id=object_id,
                reason=reason,
                reporter_session_key=session_key
            )
        elif content_type == 'reply':
            ReplyReport.objects.create(
                reply_id=object_id,
                reason=reason,
                reporter_session_key=session_key
            )
        return redirect('done_report')

    return render(request, 'report_comment.html', {
        'content_type': content_type,
        'object_id': object_id
    })
    
@csrf_exempt
def comment_post(request, post_id):
    session_key = get_session_key(request)
    post = get_object_or_404(Post, id=post_id)

    content = request.POST.get('content', '').strip()
    image_file = request.FILES.get('image') 

    if not content and not image_file:
        return JsonResponse({"success": False, "error": "Content or image is required"})

    try:
        comment = Comment.objects.create(
            post=post,
            content=content,
            session_key=session_key,
            image=image_file, 
            is_gif=image_file.name.endswith('.gif') if image_file else False
        )

        response_data = {
            "success": True,
            "comment": {
                "id": comment.id,
                "content": comment.content,
                "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
            }
        }
        
        if post.session_key != session_key:
            Notification.objects.create(
                recipient_session_key=post.session_key,
                sender_session_key=session_key,
                notification_type='new_comment',
                post=post,
                comment=comment
            )

        if comment.image:
            response_data['comment']['image_url'] = comment.image.url
            response_data['comment']['is_gif'] = comment.is_gif

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@csrf_exempt
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    session_key = get_session_key(request)

    if request.method == "POST":
        existing_like = CommentLike.objects.filter(comment=comment, session_key=session_key).first()
        if existing_like:
            existing_like.delete()
            liked = False
        else:
            CommentLike.objects.create(comment=comment, session_key=session_key)
            liked = True
            
            if comment.session_key != session_key:
                Notification.objects.create(
                 recipient_session_key=comment.session_key,
                 sender_session_key=session_key,
                 notification_type='comment_like',
                 post=comment.post,
                 comment=comment
                )
        like_count = comment.likes.count()
        return JsonResponse({
            'success': True,
            'like_count': like_count,
            'liked': liked
        })
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@csrf_exempt
def reply_comment(request, comment_id):
    if request.method == 'POST':
        try:
            parent_comment = get_object_or_404(Comment, id=comment_id)
            session_key = get_session_key(request)
            
            reply = Reply.objects.create(
                comment=parent_comment,
                content=request.POST.get('content', ''),
                session_key=get_session_key(request),
                image=request.FILES.get('image'), 
                is_gif=request.FILES.get('image').name.endswith('.gif') if request.FILES.get('image') else False
            )
            
            if parent_comment.session_key != session_key:
                Notification.objects.create(
                 recipient_session_key=parent_comment.session_key,
                 sender_session_key=session_key,
                 notification_type='new_reply',
                 post=parent_comment.post,
                 comment=parent_comment,
                 reply=reply
                )
            return JsonResponse({
                'success': True,
                'reply': {
                    'id': reply.id,
                    'content': reply.content,
                    'image_url': reply.image.url if reply.image else None,
                    'is_gif': reply.is_gif,
                    'session_key': reply.session_key,
                    'like_count': reply.like_count
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        

@csrf_exempt
def like_reply(request, reply_id):
    reply = get_object_or_404(Reply, id=reply_id)
    session_key = get_session_key(request) 

    like_exists = ReplyLike.objects.filter(
        reply=reply,
        session_key=session_key
    ).exists()

    if like_exists:
        ReplyLike.objects.filter(reply=reply, session_key=session_key).delete()
        liked = False
    else:
        ReplyLike.objects.create(reply=reply, session_key=session_key)
        liked = True
        
        if reply.session_key != session_key:
            Notification.objects.create(
             recipient_session_key=reply.session_key,
             sender_session_key=session_key,
             notification_type='reply_like',
             post=reply.comment.post,
             comment=reply.comment,
             reply=reply
            )
    reply.like_count = ReplyLike.objects.filter(reply=reply).count()
    reply.save()

    return JsonResponse({'success': True, 'liked': liked, 'like_count': reply.like_count})


@csrf_exempt
def delete_comment(request, comment_id):
    if request.method == 'POST':
        try:
            comment = Comment.objects.get(id=comment_id)
            if comment.session_key == request.session.session_key:
                comment.delete()
                return JsonResponse({'success': 'Comment deleted successfully'})
            else:
                return JsonResponse({'error': 'Permission denied'}, status=403)

        except Comment.DoesNotExist:
            return JsonResponse({'error': 'Comment not found'}, status=404)
        

@csrf_exempt
def delete_reply(request, reply_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST allowed'}, status=405)
    try:
        reply = get_object_or_404(Reply, id=reply_id)
        session_key = get_session_key(request)
        print(f"Session Key: {session_key}, Reply Session Key: {reply.session_key}")
        
        if reply.session_key != session_key:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
 
        reply.delete()
        return JsonResponse({'success': True, 'deleted_id': reply_id})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    
def get_notifications(request):
    """
    Returns notifications for the current user.
    Handles both AJAX (JSON) and direct browser (HTML) requests.
    """
    session_key = get_session_key(request)
    print(f"Debug: Fetching notifications for session_key={session_key}")

    try:
        unread_count = Notification.objects.filter(
            recipient_session_key=session_key,
            is_read=False
        ).count()

        notifications = Notification.objects.filter(
            recipient_session_key=session_key
        ).select_related('post', 'comment', 'reply').order_by('-created_at')[:20]

        print(f"Debug: Found {notifications.count()} notifications")

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            notifications_data = [{
                'id': n.id,
                'type': n.notification_type,
                'is_read': n.is_read,
                'created_at': n.created_at.strftime("%Y-%m-%d %H:%M"),
                'message': generate_notification_message(n)
            } for n in notifications]
            
            return JsonResponse({
                'notifications': notifications_data,
                'unread_count': unread_count
            })
            
        return render(request, 'notification.html', {
            'notifications': notifications,
            'unread_count': unread_count
        })

    except Exception as e:
        print(f"Error fetching notifications: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Server error'}, status=500)
        return render(request, 'notification.html', {
            'error': 'Failed to load notifications',
            'unread_count': 0
        })


def mark_as_read(request, notification_id):
    """
    Marks a notification as read.
    Requires AJAX request with notification ID.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        session_key = get_session_key(request)
        print(f"Debug: Marking notification {notification_id} as read for session={session_key}")  # Debug log
        
        notification = Notification.objects.get(
            id=notification_id,
            recipient_session_key=session_key
        )
        
        if not notification.is_read:
            notification.is_read = True
            notification.save()
            print(f"Debug: Notification {notification_id} marked as read")  # Debug log
            
        return JsonResponse({'success': True, 'is_read': True})
        
    except Notification.DoesNotExist:
        print(f"Debug: Notification {notification_id} not found for session={session_key}")  # Debug log
        return JsonResponse({'error': 'Notification not found'}, status=404)
    except Exception as e:
        print(f"Error marking notification as read: {str(e)}")  # Debug log
        return JsonResponse({'error': str(e)}, status=500)


def generate_notification_message(notification):
    """
    Generates human-readable notification messages with emojis.
    """
    if notification.notification_type == 'post_like':
        return f"👍 Someone liked your post: '{notification.post.title}'"
    elif notification.notification_type == 'comment_like':
        content = notification.comment.content[:30] + '...' if len(notification.comment.content) > 30 else notification.comment.content
        return f"👍 Someone liked your comment: '{content}'"
    elif notification.notification_type == 'reply_like':
        return "👍 Someone liked your reply"
    elif notification.notification_type == 'new_comment':
        return f"💬 New comment on your post: '{notification.post.title}'"
    elif notification.notification_type == 'new_reply':
        return "↪️ New reply to your comment"
    return "🔔 You have a new notification"