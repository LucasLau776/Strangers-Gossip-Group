from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from .models import Post, Comment, PostLike, CommentLike, Reply, ReplyLike, PostSave, PostReport, CommentReport, SessionIdentity
from django import template


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
    comments = post.comments.all()
    comments = Comment.objects.filter(post=post).order_by('-created_at')

    for comment in comments:
        comment.current_session_key = request.session.session_key

    liked = PostLike.objects.filter(post=post, session_key=session_key).exists()
    saved = PostSave.objects.filter(post=post, session_key=session_key).exists()
    post_like_count = PostLike.objects.filter(post=post).count()
    total_comments = comments.count()

    return render(request, "full_post.html", {
        'post': post,
        'liked': liked,
        'saved': saved,
        'post_like_count': post_like_count,
        'comments': comments,
        'total_comments': total_comments,
        'session_key': request.session.session_key,
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


@csrf_exempt
def like_post(request, post_id):
    session_key = get_session_key(request)
    post = get_object_or_404(Post, id=post_id)
    like, created = PostLike.objects.get_or_create(post=post, session_key=session_key)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    like_count = PostLike.objects.filter(post=post).count()
    return JsonResponse({
        "liked": liked,
        "like_count": like_count,
    })

@csrf_exempt
def report_post(request, post_id):
    if request.method == 'POST':
        reason = request.POST.get('reason')
        session_key = get_session_key(request)
        PostReport.objects.create(post_id=post_id, reason=reason, session_key=session_key)
        return redirect('done_report')
    return render(request, 'report.html', {'post_id': post_id})


@csrf_exempt
def report_comment(request, comment_id):
    if request.method == 'POST':
        reason = request.POST.get('reason')
        session_key = get_session_key(request)
        CommentReport.objects.create(comment_id=comment_id, reason=reason, session_key=session_key)
        return redirect('done_report')
    return render(request, 'report_comment.html', {'comment_id': comment_id})


@csrf_exempt
def comment_post(request, post_id):
    session_key = get_session_key(request)
    post = get_object_or_404(Post, id=post_id)
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({"success": False, "error": "Content cannot be empty"})
    try:
        comment = Comment.objects.create(post=post, content=content, session_key=session_key)
        return JsonResponse({
            "success": True,
            "comment": {
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at,
            }
        })
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
            print("Request Body:", request.body)
            data = json.loads(request.body)
            content = data.get('content')
            if not content:
                return JsonResponse({'error': 'Content cannot be empty'}, status=400)
            parent_comment = get_object_or_404(Comment, id=comment_id)
            new_reply = Reply.objects.create(
                comment=parent_comment,
                content=content,
                session_key=request.session.session_key
            )

            return JsonResponse({
                'success': True,
                'reply': {
                    'id': new_reply.id,
                    'content': new_reply.content,
                    'created_at': new_reply.created_at.isoformat(),
                    'session_key': new_reply.session_key,
                    'like_count': new_reply.like_count
                }
            })

        except Exception as e:
            print("Error:", str(e))
            return JsonResponse({'error': str(e)}, status=400)
        

@csrf_exempt
def like_reply(request, reply_id):
    session_key = get_session_key(request)
    reply = get_object_or_404(Reply, id=reply_id)
    if ReplyLike.objects.filter(reply=reply, session_key=session_key).exists():
        return JsonResponse({"success": False, "error": "Already liked"})
    ReplyLike.objects.create(reply=reply, session_key=session_key)
    return JsonResponse({"success": True, "like_count": reply.likes.count()})


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