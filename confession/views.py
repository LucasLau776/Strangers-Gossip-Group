from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import now

from .models import Confession, Comment, Like, CommentLike, UserProfile


# 用户注册视图
def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]

        if not (email.endswith("@student.mmu.edu.my") or email.endswith("@mmu.edu.my")):
            return render(request, "confession/register.html", {
                "error": "Only MMU email addresses are allowed."
            })

        if User.objects.filter(username=username).exists():
            return render(request, "confession/register.html", {
                "error": "Username already exists."
            })

        # ❌ 不再手动创建 UserProfile，signals.py 会自动创建
        User.objects.create_user(username=username, email=email, password=password)
        return redirect('login')

    return render(request, "confession/register.html")

# 用户登录视
def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return render(request, "confession/login.html", {"error": "Invalid username or password."})
    return render(request, "confession/login.html")


# 用户登出视图
def logout_view(request):
    logout(request)
    return redirect('index')


# 发布新表白（带 cooldown 限制）
@login_required
def post_confession(request):
    profile = get_object_or_404(UserProfile, user=request.user)

    if request.method == "POST":
        content = request.POST.get("content")
        if profile.last_post_time and now() - profile.last_post_time < timedelta(seconds=60):
            wait_seconds = 60 - int((now() - profile.last_post_time).total_seconds())
            return render(request, 'confession/post.html', {
                'error': f'Please wait {wait_seconds} seconds before posting again.'
            })

        if content:
            Confession.objects.create(
                content=content,
                user=request.user.username
            )
            profile.last_post_time = now()
            profile.save()
            return redirect('index')
        else:
            return render(request, 'confession/post.html', {'error': 'Content cannot be empty.'})
    return render(request, 'confession/post.html')


# 表白列表页
def confession_list_view(request):
    confessions = Confession.objects.filter(is_deleted=False).order_by('-timestamp')
    return render(request, 'confession/index.html', {'confessions': confessions})


# 表白详情页（包含评论与子评论）
def full_post_view(request, confession_id):
    confession = get_object_or_404(Confession, id=confession_id)
    all_comments = Comment.objects.filter(confession=confession).select_related('parent').order_by('timestamp')

    comment_dict = {}
    for comment in all_comments:
        comment.child_comments = []
        comment_dict[comment.id] = comment

    top_level_comments = []
    for comment in all_comments:
        if comment.parent_id:
            parent = comment_dict.get(comment.parent_id)
            if parent:
                parent.child_comments.append(comment)
        else:
            top_level_comments.append(comment)

    liked_comment_ids = []
    if request.user.is_authenticated:
        liked_comment_ids = list(
            CommentLike.objects.filter(user=request.user, comment__confession=confession).values_list('comment_id', flat=True)
        )
        already_liked = Like.objects.filter(user=request.user, confession=confession).exists()
    else:
        already_liked = False

    return render(request, 'confession/full_post.html', {
        'confession': confession,
        'comments': top_level_comments,
        'already_liked': already_liked,
        'liked_comment_ids': liked_comment_ids,
    })


# 提交评论/回复
def comment_view(request, confession_id):
    confession = get_object_or_404(Confession, id=confession_id)

    if request.method == "POST":
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')

        parent_comment = None
        if parent_id and parent_id.isdigit():
            try:
                parent_comment = Comment.objects.get(id=int(parent_id))
            except Comment.DoesNotExist:
                parent_comment = None

        if content:
            Comment.objects.create(
                confession=confession,
                content=content,
                user=request.user.username,
                parent=parent_comment
            )
        return redirect('full_post', confession_id=confession_id)
    return redirect('full_post', confession_id=confession_id)


# 点赞 confession
@login_required
def like_confession(request, confession_id):
    confession = get_object_or_404(Confession, id=confession_id)
    already_liked = Like.objects.filter(user=request.user, confession=confession).exists()

    if not already_liked:
        Like.objects.create(user=request.user, confession=confession)
        confession.upvotes += 1
        confession.save()

    return redirect('full_post', confession_id=confession.id)


# 热门表白
def trending_view(request):
    confessions = Confession.objects.filter(is_deleted=False).order_by('-upvotes', '-timestamp')
    return render(request, 'confession/trending.html', {'confessions': confessions})


# 搜索功能
def search_view(request):
    query = request.GET.get('q')
    filter_type = request.GET.get('filter')

    results = Confession.objects.filter(content__icontains=query, is_deleted=False)

    if filter_type == 'date':
        results = results.order_by('-timestamp')
    elif filter_type == 'popularity':
        results = results.order_by('-upvotes', '-timestamp')
    elif filter_type == 'year':
        results = results.filter(timestamp__year=timezone.now().year).order_by('-timestamp')

    return render(request, 'confession/search_results.html', {
        'confessions': results,
        'query': query,
        'filter_type': filter_type,
    })


# 点赞评论
@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if not CommentLike.objects.filter(user=request.user, comment=comment).exists():
        CommentLike.objects.create(user=request.user, comment=comment)
        comment.upvotes += 1
        comment.save()

    return redirect('full_post', confession_id=comment.confession.id)
