from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from .models import Post, Comment, Reply, PostLike, CommentLike, ReplyLike, Report, Confession, Save, Notification
from django.db.models import Count
from datetime import datetime
from .forms import PostForm, MMURegisterForm
from django.http import  JsonResponse,HttpResponseBadRequest


def home(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'confession/index.html', {'posts': posts})

def post_confession(request):
    return render(request, 'confession/post.html')

def register_view(request):
    if request.method == 'POST':
        form = MMURegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.save()
            return redirect('login')
    else:
        form = MMURegisterForm()
    return render(request, 'confession/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'confession/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def submit_post_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.session_key = request.session.session_key or 'anonymous'
            post.save()
            return redirect('home')
    else:
        form = PostForm()
    return render(request, 'confession/post.html', {'form': form})

def full_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post, parent=None).order_by('-created_at')
    session_key = request.session.session_key or "anonymous"
    is_saved = Save.objects.filter(post=post, session_key=session_key).exists()
    return render(request, 'confession/full_post.html', {'is_saved': is_saved, 'post': post, 'comments': comments})

def trending_view(request):
    trending_posts = Post.objects.annotate(
    like_count=Count('likes')  # 正确字段是 'likes'，不是 'postlike'
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

@require_POST
@csrf_exempt
def like_post(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        post_id = request.POST.get('post_id')
        session_key = request.session.session_key or "anonymous"
        post = get_object_or_404(Post, id=post_id)
        liked = PostLike.objects.filter(post=post, session_key=session_key)

        if liked.exists():
            liked.delete()
            post.likes_count -= 1
            liked_status = False
        else:
            PostLike.objects.create(post=post, session_key=session_key)
            post.likes_count += 1
            liked_status = True

        post.save()
        return JsonResponse({'success': True, 'liked': liked_status, 'like_count': post.likes_count})
    return JsonResponse({'success': False})

@require_POST
@csrf_exempt
def add_comment(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        post_id = request.POST.get('post_id')
        content = request.POST.get('content')
        session_key = request.session.session_key or "anonymous"
        image = request.FILES.get('image', None)
        is_gif = image.name.lower().endswith('.gif') if image else False

        post = get_object_or_404(Post, id=post_id)
        comment = Comment.objects.create(
        post=post,
        content=content,
        session_key=session_key,
        user=request.user if request.user.is_authenticated else None,
        image=image,
        is_gif=is_gif,
        parent=None
      )

        return JsonResponse({
            'success': True,
            'comment_id': comment.id,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    return JsonResponse({'success': False})

@require_POST
@csrf_exempt
def add_reply(request):
    print("🔥 add_reply view called")

    comment_id = request.POST.get('comment_id')
    content = request.POST.get('content')
    session_key = request.session.session_key or "anonymous"
    image = request.FILES.get('image', None)
    is_gif = image.name.lower().endswith('.gif') if image else False

    print("🧪 comment_id =", comment_id)
    print("🧪 content =", content)
    print("🧪 session_key =", session_key)

    if not comment_id or not content:
        print("❌ Missing comment_id or content")
        return JsonResponse({'success': False, 'error': 'Missing data'}, status=400)

    try:
        comment = get_object_or_404(Comment, id=comment_id)
        reply = Reply.objects.create(
            comment=comment,
            content=content,
            session_key=session_key,
            user=request.user if request.user.is_authenticated else None,
            image=image,
            is_gif=is_gif
        )
        print("✅ Reply created:", reply)
        return JsonResponse({'success': True})
    except Exception as e:
        print("❌ Exception:", str(e))
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@csrf_exempt
def like_comment(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        comment_id = request.POST.get('comment_id')
        session_key = request.session.session_key or "anonymous"
        comment = get_object_or_404(Comment, id=comment_id)
        liked = CommentLike.objects.filter(comment=comment, session_key=session_key)

        if liked.exists():
            liked.delete()
            comment.like_count -= 1
            liked_status = False
        else:
            CommentLike.objects.create(comment=comment, session_key=session_key)
            comment.like_count += 1
            liked_status = True

        comment.save()
        return JsonResponse({'success': True, 'liked': liked_status, 'like_count': comment.like_count})
    return JsonResponse({'success': False})

@require_POST
@csrf_exempt
def like_reply(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        reply_id = request.POST.get('reply_id')
        session_key = request.session.session_key or "anonymous"
        reply = get_object_or_404(Reply, id=reply_id)
        liked = ReplyLike.objects.filter(reply=reply, session_key=session_key)

        if liked.exists():
            liked.delete()
            reply.like_count -= 1
            liked_status = False
        else:
            ReplyLike.objects.create(reply=reply, session_key=session_key)
            reply.like_count += 1
            liked_status = True

        reply.save()
        return JsonResponse({'success': True, 'liked': liked_status, 'like_count': reply.like_count})
    return JsonResponse({'success': False})

@require_POST
@csrf_exempt
def like_confession(request, confession_id):
    confession = get_object_or_404(Confession, id=confession_id)
    confession.upvotes += 1
    confession.save()
    return JsonResponse({'success': True, 'upvotes': confession.upvotes})

@csrf_exempt
def comment_post(request, confession_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        session_key = request.session.session_key or "anonymous"
        confession = get_object_or_404(Confession, id=confession_id)
        # ✅ 修正 post=confession => post is None
        Comment.objects.create(
            content=content,
            session_key=session_key,
            post=None
        )
        return redirect('full_post', post_id=confession_id)
    return JsonResponse({'error': 'Only POST allowed'}, status=400)

@csrf_exempt
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.delete()
    return JsonResponse({'success': True})

@csrf_exempt
def reply_comment(request, comment_id):
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
def delete_reply(request, reply_id):
    reply = get_object_or_404(Reply, id=reply_id)
    reply.delete()
    return JsonResponse({'success': True})

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

def bookmark_view(request):
    session_key = request.session.session_key or "anonymous"
    saved_posts = Save.objects.filter(session_key=session_key).select_related('post')
    return render(request, 'confession/bookmark.html', {'saved_posts': saved_posts})

@csrf_exempt
def report_view(request, content_type, object_id):
    if request.method == 'POST':
        reason = request.POST.get('reason')
        if reason:
            try:
                # ✅ 获取 ContentType 实例
                model_type = ContentType.objects.get(model=content_type)

                # ✅ 创建 Report 实例
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

    # ✅ GET 请求渲染举报表单
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

def get_notifications(request):
    session_key = request.session.session_key or 'anonymous'
    notifications = Notification.objects.filter(session_key=session_key).order_by('-created_at')
    return render(request, 'confession/notifications.html', {'notifications': notifications})

@csrf_exempt
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})

def custom_404(request, exception):
    return render(request, 'confession/404.html', status=404)

def custom_500(request):
    return render(request, 'confession/500.html', status=500)

@csrf_exempt
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})

@csrf_exempt
@require_POST
def unsave_post(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        post_id = request.POST.get('post_id')
        session_key = request.session.session_key or "anonymous"
        Save.objects.filter(post_id=post_id, session_key=session_key).delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})
