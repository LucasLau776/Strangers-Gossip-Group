from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from .models import (
    Post, PostLike, Comment, CommentLike, Reply, ReplyLike,
    Report, Save, Notification, UserProfile, SessionIdentity
)
from .forms import PostForm, CommentForm
import json
from datetime import timedelta

def index(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'confession/index.html', {'posts': posts})

@login_required
def post_confession(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.session_key = request.session.session_key
            post.user = request.user
            post.save()
            return redirect('index')
    else:
        form = PostForm()
    return render(request, 'confession/post.html', {'form': form})

def full_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post, parent=None).order_by('-created_at')
    return render(request, 'confession/full_post.html', {'post': post, 'comments': comments})

@require_POST
@csrf_exempt
def like_confession(request, confession_id):
    post = get_object_or_404(Post, id=confession_id)
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key
    existing_like = PostLike.objects.filter(post=post, session_key=session_key).first()
    if existing_like:
        existing_like.delete()
        post.likes_count -= 1
        liked = False
    else:
        PostLike.objects.create(post=post, session_key=session_key)
        post.likes_count += 1
        liked = True
    post.save()
    return JsonResponse({'success': True, 'liked': liked, 'likes_count': post.likes_count})

@require_POST
@csrf_exempt
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key
    existing_like = CommentLike.objects.filter(comment=comment, session_key=session_key).first()
    if existing_like:
        existing_like.delete()
        comment.likes_count -= 1
        liked = False
    else:
        CommentLike.objects.create(comment=comment, session_key=session_key)
        comment.likes_count += 1
        liked = True
    comment.save()
    return JsonResponse({'success': True, 'liked': liked, 'likes_count': comment.likes_count})

@require_POST
@csrf_exempt
def like_reply(request, reply_id):
    reply = get_object_or_404(Reply, id=reply_id)
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key
    existing_like = ReplyLike.objects.filter(reply=reply, session_key=session_key).first()
    if existing_like:
        existing_like.delete()
        reply.likes_count -= 1
        liked = False
    else:
        ReplyLike.objects.create(reply=reply, session_key=session_key)
        reply.likes_count += 1
        liked = True
    reply.save()
    return JsonResponse({'success': True, 'liked': liked, 'likes_count': reply.likes_count})

@login_required
@require_POST
@csrf_exempt
def submit_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'success': False, 'error': 'Comment content cannot be empty'}, status=400)
    comment = Comment.objects.create(
        post=post,
        content=content,
        user=user,
        session_key=request.session.session_key
    )
    return JsonResponse({'success': True, 'comment_id': comment.id})

@login_required
@require_POST
@csrf_exempt
def submit_reply(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    user = request.user
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'success': False, 'error': 'Reply content cannot be empty'}, status=400)
    reply = Reply.objects.create(
        comment=comment,
        content=content,
        user=user,
        session_key=request.session.session_key
    )
    return JsonResponse({'success': True, 'reply_id': reply.id})

@login_required
@require_POST
@csrf_exempt
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    session_key = request.session.session_key
    if (request.user.is_authenticated and post.user == request.user) or (session_key and post.session_key == session_key):
        post.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

@login_required
@require_POST
@csrf_exempt
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    session_key = request.session.session_key
    if (request.user.is_authenticated and comment.user == request.user) or (session_key and comment.session_key == session_key):
        comment.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

@login_required
@require_POST
@csrf_exempt
def delete_reply(request, reply_id):
    reply = get_object_or_404(Reply, id=reply_id)
    session_key = request.session.session_key
    if (request.user.is_authenticated and reply.user == request.user) or (session_key and reply.session_key == session_key):
        reply.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)