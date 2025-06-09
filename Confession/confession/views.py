from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.urls import reverse
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from .models import Post, Comment, Reply, PostLike, CommentLike, ReplyLike, Report, Confession, Save, Notification, UserProfile, PasswordChangeLog, AvatarChangeLog
from django.db import models
from django.db.models import Count
from datetime import datetime
from .forms import PostForm, MMURegisterForm, MMUAuthenticationForm, ProfileForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
import json
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
from django.templatetags.static import static
import logging
import time
from django.conf import settings
from django.db.models import Q

logger = logging.getLogger(__name__)

def is_user_banned(user):
    if not user.is_authenticated:
        return False
    try:
        return user.userprofile.is_currently_banned
    except UserProfile.DoesNotExist:
        return False

def home(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'confession/index.html', {'posts': posts})

def post(request):
    return render(request, 'confession/post.html')

def notifications(request):
    return render(request, 'confession/notifications.html')

def register_view(request):
    next_url = request.GET.get('next', '')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = 'home'
        
    if request.user.is_authenticated:
        return redirect(next_url)
        
    if request.method == 'POST':
        form = MMURegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(next_url)
    else:
        email = request.GET.get('email')
        if email:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'This email is already registered. Please login.')
                return redirect(f"{reverse('login')}?next={next_url}")
        form = MMURegisterForm()

    return render(request, 'confession/register.html', {
        'form': form,
        'next': next_url
    })

@require_http_methods(["GET", "POST"])
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    next_url = request.GET.get('next', 'home')
    
    if request.method == 'POST':
        form = MMUAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Enhanced ban check
            if is_user_banned(user):
                try:
                    profile = user.userprofile
                    ban_message = "Your account is currently banned."
                    if profile.ban_reason:
                        ban_message += f" Reason: {profile.ban_reason}"
                    if profile.ban_expiry:
                        ban_message += f" Ban expires on: {profile.ban_expiry.strftime('%Y-%m-%d %H:%M')}"
                    messages.error(request, ban_message)
                except UserProfile.DoesNotExist:
                    messages.error(request, "Your account is currently banned.")
                return redirect('login')
                
            login(request, user)
            return redirect(next_url)
        else:
            messages.error(request, form.error_messages['invalid_login'])
            return redirect(f"{reverse('register')}?next={next_url}")
    else:
        form = MMUAuthenticationForm(request)
    
    return render(request, 'confession/login.html', {
        'form': form,
        'next': next_url
    })

def banned_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
        
    try:
        profile = request.user.userprofile
        context = {
            'is_banned': profile.is_currently_banned,
            'ban_reason': profile.ban_reason,
            'ban_expiry': profile.ban_expiry,
        }
        return render(request, 'confession/banned.html', context)
    except UserProfile.DoesNotExist:
        return redirect('home')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='/login/')
def submit_post_view(request):
    if is_user_banned(request.user):
        return JsonResponse({"success": False, "error": "You are banned from performing this action."}, status=403)

    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data.get("title", "")
            content = form.cleaned_data.get("content", "")

            if contains_toxic_words(title) or contains_toxic_words(content):
                return JsonResponse({"success": False, "error": "Toxic content is not allowed."}, status=400)

            post = form.save(commit=False)
            post.user = request.user
            post.session_key = request.session.session_key
            post.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "error": "Invalid form data."}, status=400)
    else:
        form = PostForm()

    return render(request, 'confession/post.html', {
        'form': form,
        'user': request.user
    })

def full_post(request, post_id):
    post = get_object_or_404(Post.objects.select_related('user__userprofile'), id=post_id)
    comments = Comment.objects.filter(post=post, parent=None).order_by('-created_at')

    is_authenticated = request.user.is_authenticated
    session_key = request.session.session_key or "anonymous"

    post_avatar = None
    if post.user:
        try:
            user_profile = UserProfile.objects.get(user=post.user)
            if user_profile.avatar:
                post_avatar = static(f'avatars/{user_profile.avatar}')
        except UserProfile.DoesNotExist:
            pass

    is_saved = False
    if is_authenticated:
        is_saved = Save.objects.filter(post=post, session_key=session_key).exists()

    post.views += 1
    post.save()
    
    return render(request, 'confession/full_post.html', {
        'post': post,
        'post_avatar': post_avatar,
        'comments': comments,
        'is_saved': is_saved,
        'user_is_authenticated': is_authenticated,
        'current_user_session_key': session_key,
    })

    
COOLDOWN_SECONDS = 60

@csrf_exempt
@require_POST
def ajax_post_confession(request):
    session_key = request.session.session_key or request.session.save() or request.session.session_key
    now = int(time.time())
    last_post_time = request.session.get('last_post_time', 0)

    if hasattr(request.user, 'userprofile') and request.user.userprofile.is_banned:
        return JsonResponse({'success': False, 'error': 'You have been banned.'}, status=403)


    if now - last_post_time < COOLDOWN_SECONDS:
        return JsonResponse({'cooldown': True, 'seconds_left': COOLDOWN_SECONDS - (now - last_post_time)})

    title = request.POST.get('title')or ""
    content = request.POST.get('content')or ""

    if contains_toxic_words(title) or contains_toxic_words(content):
        return JsonResponse({"success": False, "error": "Toxic content is not allowed."}, status=400)

    if not title or not content:
        return JsonResponse({'error': 'Title and content are required.'})

    Post.objects.create(
        title=title,
        content=content,
        session_key=session_key,
        user=request.user if request.user.is_authenticated else None
    )
    request.session['last_post_time'] = now

    return JsonResponse({'success': True})

# Trending and Search
def trending_view(request):
    trending_posts = Post.objects.annotate(
        like_count=Count('likes')
    ).order_by('-like_count', '-created_at')[:50]
    return render(request, 'confession/trending.html', {'trending_posts': trending_posts})

def search_view(request):
    query = request.GET.get('q')
    filter_type = request.GET.get('filter', 'date')
    results = Post.objects.filter(title__icontains=query)

    if filter_type == 'popularity':
        results = results.order_by('-likes_count')
    elif filter_type == 'year':
        results = results.filter(created_at__year=datetime.now().year)
    else:
        results = results.order_by('-created_at')

    return render(request, 'confession/search_results.html', {
        'query': query,
        'results': results,
        'filter_type': filter_type,
    })

# Profile views
@login_required
def profile(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    context = {
        'user': user,
        'user_profile': user_profile,
    }
    return render(request, 'confession/profile.html', context)

@csrf_exempt
@login_required
@require_http_methods(["GET", "POST"])
def edit_profile(request):
    user = request.user
    profile = user.userprofile

    if request.method == 'GET':
        avatar_choices = [f"avatar{i}.png" for i in range(1, 29)]
        return render(request, 'confession/edit_profile.html', {
            'user': user,
            'user_profile': profile,
            'avatar_choices': avatar_choices
        })

    try:
        new_avatar = request.POST.get('avatar')
        current_password = request.POST.get('currentPassword')
        new_password = request.POST.get('newPassword')
        confirm_password = request.POST.get('confirmPassword')

        response = {'success': True}

        if new_avatar:
            profile.avatar = new_avatar
            profile.save()
            response['avatar_url'] = profile.avatar.url if hasattr(profile.avatar, 'url') else f"/static/avatars/{profile.avatar}"

        if new_password:
            if not current_password or not user.check_password(current_password):
                return JsonResponse({'success': False, 'error': 'Current password is incorrect'}, status=400)
            if new_password != confirm_password:
                return JsonResponse({'success': False, 'error': 'New passwords do not match'}, status=400)
            if len(new_password) < 8:
                return JsonResponse({'success': False, 'error': 'New password must be at least 8 characters'}, status=400)

            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            response['password_changed'] = True

        return JsonResponse(response)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# AJAX Profile Updates
@login_required
@require_POST
@csrf_exempt
def update_password(request):
    current_password = request.POST.get('current_password', '')
    new_password = request.POST.get('new_password', '')
    confirm_password = request.POST.get('confirm_password', '')
    
    if not request.user.check_password(current_password):
        return JsonResponse({'success': False, 'error': 'Current password is incorrect'})
        
    if new_password != confirm_password:
        return JsonResponse({'success': False, 'error': 'Passwords do not match'})
        
    if len(new_password) < 8:
        return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters'})
        
    request.user.set_password(new_password)
    request.user.save()
    update_session_auth_hash(request, request.user)
    return JsonResponse({'success': True})

@login_required
@require_POST
def update_avatar(request):
    avatar = request.POST.get('avatar', '')
    valid_avatars = [f'avatar{i}.png' for i in range(1, 29)]
    
    if avatar not in valid_avatars:
        return JsonResponse({'success': False, 'error': 'Invalid avatar selection'})
        
    profile = get_object_or_404(UserProfile, user=request.user)
    profile.avatar = avatar
    profile.save()
    return JsonResponse({'success': True, 'avatar_url': profile.avatar.url})

@login_required
@require_POST
@csrf_exempt
def update_theme(request):
    dark_mode = request.POST.get('dark_mode', 'false') == 'true'
    profile = get_object_or_404(UserProfile, user=request.user)
    profile.dark_mode = dark_mode
    profile.save()
    return JsonResponse({'success': True})

# AJAX Content Interaction Views
@csrf_exempt
@require_POST
@login_required
def like_post(request):
    if is_user_banned(request.user):
     return JsonResponse({"success": False, "error": "You are banned from performing this action."}, status=403)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        post_id = request.POST.get('post_id')
        session_key = request.session.session_key or "anonymous"
        post = get_object_or_404(Post, id=post_id)
        liked = PostLike.objects.filter(post=post, session_key=session_key)

        if liked.exists():
            liked.delete()
            liked_status = False
        else:
            PostLike.objects.create(post=post, session_key=session_key)
            liked_status = True
            notify_user_of_like(post, request.user if request.user.is_authenticated else None, session_key)

        like_count = PostLike.objects.filter(post=post).count()
        post.likes_count = like_count
        post.save(update_fields=['likes_count'])

        return JsonResponse({'success': True, 'liked': liked_status, 'like_count': like_count})
    return JsonResponse({'success': False})

@csrf_exempt
@require_POST
@login_required
def like_comment(request):
    if hasattr(request.user, 'userprofile') and request.user.userprofile.is_banned:
        return JsonResponse({'success': False, 'error': 'You have been banned.'}, status=403)
    if is_user_banned(request.user):
     return JsonResponse({"success": False, "error": "You are banned from performing this action."}, status=403)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        comment_id = request.POST.get('comment_id')
        session_key = request.session.session_key or "anonymous"
        comment = get_object_or_404(Comment, id=comment_id)
        liked = CommentLike.objects.filter(comment=comment, session_key=session_key)

        if liked.exists():
            liked.delete()
            liked_status = False
        else:
            CommentLike.objects.create(comment=comment, session_key=session_key)
            liked_status = True
            notify_user_of_like(comment, request.user if request.user.is_authenticated else None, session_key)

        like_count = CommentLike.objects.filter(comment=comment).count()
        comment.like_count = like_count
        comment.save(update_fields=['like_count'])

        return JsonResponse({'success': True, 'liked': liked_status, 'like_count': like_count})
    return JsonResponse({'success': False})

@require_POST
def like_reply(request):
    if is_user_banned(request.user):
        return JsonResponse({"success": False, "error": "You have been banned."}, status=403)

    reply_id = request.POST.get("reply_id")
    if not reply_id:
        return JsonResponse({"success": False, "error": "Missing reply_id"}, status=400)

    try:
        reply = Reply.objects.get(id=reply_id)
    except Reply.DoesNotExist:
        return JsonResponse({"success": False, "error": "Reply not found"}, status=404)

    session_key = request.session.session_key or request.session.save() or request.session.session_key
    like, created = ReplyLike.objects.get_or_create(reply=reply, session_key=session_key)

    if not created:
        like.delete()
        reply.likes_count = ReplyLike.objects.filter(reply=reply).count()
        reply.save()
        return JsonResponse({"success": True, "like_count": reply.likes_count})
    else:
        reply.likes_count = ReplyLike.objects.filter(reply=reply).count()
        reply.save()
        return JsonResponse({"success": True, "like_count": reply.likes_count})
    
@csrf_exempt
@require_POST
@login_required
def add_comment(request):
    if is_user_banned(request.user):
        return JsonResponse({"success": False, "error": "You have been banned."}, status=403)

    post_id = request.POST.get("post_id")
    content = request.POST.get("content", "").strip()

    if not post_id or not content:
        return JsonResponse({"success": False, "error": "Missing fields"}, status=400)

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({"success": False, "error": "Post not found"}, status=404)

    session_key = request.session.session_key or request.session.save() or request.session.session_key
    comment = Comment.objects.create(
        post=post,
        content=content,
        session_key=session_key,
        user=request.user if request.user.is_authenticated else None
    )

    return JsonResponse({"success": True, "comment_id": comment.id})

@csrf_exempt
@require_POST
@login_required
def add_reply(request):
    if is_user_banned(request.user):
     return JsonResponse({"success": False, "error": "You are banned from performing this action."}, status=403)

    try:
        session_key = request.session.session_key or "anonymous"
        logger.info("Received POST data: %s", request.POST)
        logger.info("Received FILES: %s", request.FILES)
   
        content = request.POST.get('content', '').strip()
        comment_id = request.POST.get('comment_id')
        image = request.FILES.get('image')

        if not comment_id:
            logger.error("Missing comment_id")
            return JsonResponse({
                "success": False,
                "error": "comment_id is required"
            }, status=400)

        if not content and not image:
            logger.error("Empty content and no image")
            return JsonResponse({
                "success": False,
                "error": "Either content or image is required"
            }, status=400)

        try:
            comment = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist as e:
            logger.error(f"Comment not found: {comment_id}")
            return JsonResponse({
                "success": False,
                "error": "Comment not found"
            }, status=404)

        reply = Reply.objects.create(
            comment=comment,
            content=content,
            user=request.user,
            session_key=request.session.session_key,
            image=image,
            is_gif=bool(image and image.name.lower().endswith('.gif'))
        )
        notify_user_of_new_reply(
            comment=comment,
            from_user=request.user if request.user.is_authenticated else None,
            session_key=session_key
        )
        logger.info(f"Reply created: {reply.id}")
        
        return JsonResponse({
            "success": True,
            "reply_id": reply.id,
            "content": content,
            "has_image": bool(image)
        })

    except Exception as e:
        logger.exception("Unexpected error in add_reply")
        return JsonResponse({
            "success": False,
            "error": "Internal server error",
            "detail": str(e)
        }, status=500)

def notify_user_of_new_comment(post, from_user, session_key):
    if post.user and post.user != from_user:
        Notification.create_notification(
            recipient=post.user,
            notification_type='new_comment',
            from_user=from_user,
            session_key=session_key,
            post=post,
            message=f"{from_user.username if from_user else 'Someone'} commented on your post."
        )

def notify_user_of_new_reply(comment, from_user, session_key):
    if comment.user and comment.user != from_user:
        Notification.create_notification(
            recipient=comment.user,
            notification_type='new_reply',
            from_user=from_user,
            session_key=session_key,
            comment=comment,
            message=f"{from_user.username if from_user else 'Someone'} replied to your comment."
        )
        
def notify_user_of_like(liked_obj, from_user, session_key):
    if hasattr(liked_obj, 'user') and liked_obj.user and liked_obj.user != from_user:
        notif_type = ''
        post = comment = reply = None
        
        if isinstance(liked_obj, Post):
            notif_type = 'post_like'
            post = liked_obj
        elif isinstance(liked_obj, Comment):
            notif_type = 'comment_like'
            comment = liked_obj
        elif isinstance(liked_obj, Reply):
            notif_type = 'reply_like'
            reply = liked_obj
        
        Notification.create_notification(
            recipient=liked_obj.user,
            notification_type=notif_type,
            from_user=from_user,
            session_key=session_key,
            post=post,
            comment=comment,
            reply=reply,
            message=f"{from_user.username if from_user else 'Someone'} liked your {'post' if notif_type == 'post_like' else 'comment' if notif_type == 'comment_like' else 'reply'}."
        )

@login_required
@require_POST
@csrf_exempt
def like_confession(request, confession_id):
    if hasattr(request.user, 'userprofile') and request.user.userprofile.is_banned:
        return JsonResponse({'success': False, 'error': 'You have been banned.'}, status=403)
    if is_user_banned(request.user):
        return JsonResponse({"success": False, "error": "You are banned from performing this action."}, status=403)
    
    confession = get_object_or_404(Confession, id=confession_id)
    confession.upvotes += 1
    confession.save()
    return JsonResponse({'success': True, 'upvotes': confession.upvotes})

# Comment/Reply Management
@login_required
@csrf_exempt
def comment_post(request, confession_id):
    if is_user_banned(request.user):
        return JsonResponse({"success": False, "error": "You are banned from performing this action."}, status=403)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        session_key = request.session.session_key or "anonymous"
        confession = get_object_or_404(Confession, id=confession_id)
        Comment.objects.create(
            content=content,
            session_key=session_key,
            post=None
        )
        return redirect('full_post', post_id=confession_id)
    return JsonResponse({'error': 'Only POST allowed'}, status=400)

@login_required
@csrf_exempt
@require_POST
def delete_comment(request, comment_id):
    if is_user_banned(request.user):
        return JsonResponse({"success": False, "error": "You are banned from performing this action."}, status=403)
    
    comment = get_object_or_404(Comment, id=comment_id)

    if (comment.user and comment.user == request.user) or (not comment.user and comment.session_key == request.session.session_key):
        comment.delete()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

@login_required
@csrf_exempt
def reply_comment(request, comment_id):
    if is_user_banned(request.user):
        return JsonResponse({"success": False, "error": "You are banned from performing this action."}, status=403)
    
    if request.method == 'POST':
        parent = get_object_or_404(Comment, id=comment_id)
        content = request.POST.get('content')
        session_key = request.session.session_key or "anonymous"
        Reply.objects.create(
            comment=parent,
            content=content,
            session_key=session_key
        )
        return redirect('full_post', post_id=parent.post.id)
    return JsonResponse({'error': 'Only POST allowed'}, status=400)

@csrf_exempt
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key

    if (post.user and user == post.user) or (not post.user and post.session_key == session_key):
        post.delete()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'error': "You are not allowed to delete this post."}, status=403)
    
@csrf_exempt
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    user = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key

    if (comment.user and user == comment.user) or (not comment.user and comment.session_key == session_key):
        comment.delete()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'error': "You are not allowed to delete this comment."}, status=403)

@csrf_exempt
@require_POST
def delete_reply(request, reply_id):
    reply = get_object_or_404(Reply, id=reply_id)
    user = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key

    if (reply.user and user == reply.user) or (not reply.user and reply.session_key == session_key):
        reply.delete()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'error': "You are not allowed to delete this reply."}, status=403)
    
# Bookmark
@csrf_exempt
def toggle_save_post(request, post_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        session_key = request.session.session_key or "anonymous"
        post = get_object_or_404(Post, id=post_id)
        existing = Save.objects.filter(post=post, session_key=session_key)
        if existing.exists():
            existing.delete()
            saved = False
        else:
            Save.objects.create(post=post, session_key=session_key)
            saved = True
        return JsonResponse({'success': True, 'saved': saved})
    return JsonResponse({'success': False})

@login_required
def bookmark_view(request):
    session_key = request.session.session_key or "anonymous"
    saved_posts = Save.objects.filter(session_key=session_key).select_related('post')
    return render(request, 'confession/bookmark.html', {'saved_posts': saved_posts})

@login_required
@csrf_exempt
@require_POST
def unsave_post(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        post_id = request.POST.get('post_id')
        session_key = request.session.session_key or "anonymous"
        Save.objects.filter(post_id=post_id, session_key=session_key).delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

# Report functionality
@login_required
@csrf_exempt
def report_view(request, content_type, object_id):
    if request.method == 'POST':
        reason = request.POST.get('reason')
        if reason:
            try:
                model_type = ContentType.objects.get(model=content_type)
                Report.objects.create(
                    content_type=model_type,
                    object_id=object_id,
                    reason=reason
                )
                return redirect('done_report') 
            except ContentType.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Invalid content type'}, status=400)
        else:
            return JsonResponse({'success': False, 'error': 'Missing reason'}, status=400)

    context = {}
    if content_type == 'post':
        context['post'] = get_object_or_404(Post, id=object_id)
    elif content_type == 'comment':
        context['comment'] = get_object_or_404(Comment, id=object_id)
    elif content_type == 'reply':
        context['reply'] = get_object_or_404(Reply, id=object_id)
    else:
        return HttpResponseBadRequest("Invalid content type")

    context['content_type'] = content_type
    context['object_id'] = object_id
    return render(request, 'confession/report.html', context)

def done_report_view(request):
    return render(request, 'confession/done_report.html')

# Notification
@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    unread_count = notifications.filter(is_read=False).count()

    return render(request, 'confession/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })

@login_required
@csrf_exempt
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})


# Error handlers
def custom_404(request, exception):
    return render(request, 'confession/404.html', status=404)

def custom_500(request):
    return render(request, 'confession/500.html', status=500)

@login_required
@csrf_exempt
def load_replies(request, comment_id):
    if request.method == "GET" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            comment = Comment.objects.get(id=comment_id)
            replies = comment.replies.all().order_by("created_at")

            data = []
            for reply in replies:
                data.append({
                    "id": reply.id,
                    "content": reply.content,
                    "username": reply.user.username if reply.user else f"User {reply.session_key[:5]}",
                    "like_count": reply.like_count,
                    "can_delete": (
                        request.user == reply.user or
                        (not reply.user and request.session.session_key == reply.session_key)
                    )
                })

            return JsonResponse({"success": True, "replies": data})
        except Comment.DoesNotExist:
            return JsonResponse({"success": False, "error": "Comment not found"}, status=404)
    
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip

@login_required
def build_reply_tree(replies):
    reply_dict = {reply.id: reply for reply in replies}
    tree = []

    for reply in replies:
        parent_id = reply.reply_to_id
        if parent_id and parent_id in reply_dict:
            parent = reply_dict[parent_id]
            if not hasattr(parent, 'children'):
                parent.children = []
            parent.children.append(reply)
        else:
            tree.append(reply)
    return tree

def is_admin(user):
    return user.is_authenticated and hasattr(user, 'userprofile') and user.userprofile.is_admin

@user_passes_test(is_admin)
def moderation_panel(request):
    post_type = ContentType.objects.get_for_model(Post)
    comment_type = ContentType.objects.get_for_model(Comment)

    post_reports = Report.objects.filter(content_type=post_type, resolved=False)
    comment_reports = Report.objects.filter(content_type=comment_type, resolved=False)

    reported_posts = Post.objects.filter(
        id__in=post_reports.values('object_id')
    ).annotate(
        report_count=models.Count(
            models.Case(
                models.When(report__isnull=False, then=1),
                output_field=models.IntegerField()
            )
        )
    ).order_by('-report_count')[:50]

    reported_comments = Comment.objects.filter(
        id__in=comment_reports.values('object_id')
    ).annotate(
        report_count=models.Count(
            models.Case(
                models.When(report__isnull=False, then=1),
                output_field=models.IntegerField()
            )
        )
    ).order_by('-report_count')[:50]

    for post in reported_posts:
        post.priority = 'high' if post.report_count > 5 else 'medium' if post.report_count > 2 else 'low'
        post.status = 'pending'
        post.status_display = 'Pending'

    for comment in reported_comments:
        comment.priority = 'high' if comment.report_count > 5 else 'medium' if comment.report_count > 2 else 'low'
        comment.status = 'pending'
        comment.status_display = 'Pending'

    total_reports = Report.objects.count()
    resolved_reports = Report.objects.filter(resolved=True).count()
    banned_users = UserProfile.objects.filter(is_banned=True).count()

    problem_users = User.objects.annotate(
        report_count=Count('post__report') + Count('comment__report')
    ).filter(
        Q(report_count__gt=0) | Q(userprofile__is_banned=True)
    ).distinct().select_related('userprofile')

    context = {
        'reported_posts': reported_posts,
        'reported_comments': reported_comments,
        'total_reports': total_reports,
        'pending_reports': total_reports - resolved_reports,
        'resolved_reports': resolved_reports,
        'banned_users': banned_users,
        'problem_users': problem_users,
    }
    return render(request, 'moderation_panel.html', context)

@user_passes_test(is_admin)
@require_POST
def moderation_delete(request, content_type, object_id):
    try:
        if content_type == 'post':
            obj = get_object_or_404(Post, id=object_id)
            if obj.user:
                Notification.objects.create(
                    user=obj.user,
                    session_key='system',
                    message=f"Your post '{obj.title[:20]}...' has been deleted by moderators",
                    notification_type='deleted'
                )

            Report.objects.filter(
                content_type=ContentType.objects.get_for_model(Post),
                object_id=object_id
            ).delete()
            
        elif content_type == 'comment':
            obj = get_object_or_404(Comment, id=object_id)
            if obj.user:
                Notification.objects.create(
                    user=obj.user,
                    session_key='system',
                    message=f"Your comment on post '{obj.post.title[:20]}...' has been deleted",
                    notification_type='deleted'
                )

            Report.objects.filter(
                content_type=ContentType.objects.get_for_model(Comment),
                object_id=object_id
            ).delete()
        
        obj.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@user_passes_test(is_admin)
@require_POST
def moderation_dismiss(request, content_type, object_id):
    try:
        if content_type == 'post':
            content_type = ContentType.objects.get_for_model(Post)
            get_object_or_404(Post, id=object_id)
        elif content_type == 'comment':
            content_type = ContentType.objects.get_for_model(Comment)
            get_object_or_404(Comment, id=object_id)
        
        data = json.loads(request.body)
        remove = data.get('remove', False)
        
        if remove:
            return JsonResponse({'success': True})
        
        updated = Report.objects.filter(
            content_type=content_type,
            object_id=object_id,
            resolved=False
        ).update(resolved=True)
        
        return JsonResponse({
            'success': True,
            'updated_count': updated
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@user_passes_test(is_admin)
@require_POST
@csrf_exempt
def moderation_dismiss_user(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)
        profile = user.userprofile
        profile.dismissed = True
        profile.dismissed_at = timezone.now()
        profile.dismissed_by = request.user
        profile.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@user_passes_test(is_admin)
@require_POST
def moderation_warn(request, user_id):
    try:
        data = json.loads(request.body)
        reason = data.get('reason', 'No reason provided')
        user = get_object_or_404(User, id=user_id)
        
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.add_warning(reason)
        profile.save()  # Make sure to save the profile
        
        # Create notification
        Notification.objects.create(
            user=user,
            session_key='system',
            message=f"You received a warning from moderators: {reason}",
            notification_type='warning'
        )
        
        return JsonResponse({
            'success': True,
            'warning_count': profile.warning_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
@user_passes_test(is_admin)
@require_POST
def moderation_ban(request, user_id):
    try:
        data = json.loads(request.body)
        reason = data.get('reason', 'No reason provided')
        duration = data.get('duration', 7)  # Default 7 days
        
        user = get_object_or_404(User, id=user_id)
        profile = user.userprofile
        
        profile.is_banned = True
        profile.ban_reason = reason
        profile.ban_expiry = timezone.now() + timedelta(days=int(duration))
        profile.save()
        
        Notification.objects.create(
            user=user,
            session_key='system',
            message=f"You have been banned for: {reason}. Ban expires on {profile.ban_expiry.strftime('%Y-%m-%d')}",
            notification_type='ban'
        )
        
        return JsonResponse({
            'success': True,
            'ban_expiry': profile.ban_expiry.strftime('%Y-%m-%d')
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@user_passes_test(is_admin)
@require_POST
def moderation_unban(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)
        profile = user.userprofile
        
        profile.is_banned = False
        profile.ban_reason = None
        profile.ban_expiry = None
        profile.save()
        
        Notification.objects.create(
            user=user,
            session_key='system',
            message="Your ban has been lifted by moderators",
            notification_type='unban'
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
# ==== Utility: Detect Toxic Words ====
TOXIC_WORDS = ["kill", "hate", "stupid", "idiot", "dumb", "shut up", "bastard", "ugly", "trash", "die"]

def contains_toxic_words(text):
    lowered = text.lower()
    return any(word in lowered for word in TOXIC_WORDS)

@require_POST
@login_required
def dismiss_user_report(request, user_id):
    try:
        profile = UserProfile.objects.get(user__id=user_id)
        profile.dismissed = True
        profile.dismissed_at = timezone.now()
        profile.save()
        return JsonResponse({'success': True})
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'UserProfile not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})