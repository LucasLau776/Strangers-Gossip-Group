from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Confession, Comment
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Q

def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        if User.objects.filter(username=username).exists():
            return render(request, "confession/register.html", {"error": "Username already exists."})
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return HttpResponse("Registration successful!")
    return render(request, "confession/register.html")  

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponse("Login successful!")
        else:
            return HttpResponse("Invalid username or password.")
    return render(request, "confession/login.html")  

def logout_view(request):
    logout(request)
    return HttpResponse("Logged out successfully.")

def comment_view(request, confession_id):
    if request.method == "POST":
        content = request.POST.get("content")
        user = request.POST.get("user")
        parent_id = request.POST.get("parent")
        try:
            confession = Confession.objects.get(id=confession_id)
        except Confession.DoesNotExist:
            return HttpResponse("Confession not found.")
        parent_comment = Comment.objects.get(id=parent_id) if parent_id else None
        if content and user:
            Comment.objects.create(
                confession=confession,
                content=content,
                user=user,
                parent=parent_comment
            )
            return HttpResponse("Comment submitted!")
        else:
            return HttpResponse("Missing content or user.")
    return HttpResponse("Comment page (GET)")

def post_confession_view(request):
    if request.method == "POST":
        content = request.POST.get("content")
        user = request.user.username  # 已登录的用户名
        
        if content:
            Confession.objects.create(content=content, user=user)
            return HttpResponse("Confession posted successfully!")  # 简单先返回
        else:
            return HttpResponse("Please enter some content.")
    
    return render(request, "confession/post.html")

@login_required
def post_confession(request):
    if request.method == "POST":
        content = request.POST.get("content")
        if content:
            Confession.objects.create(
                content=content,
                user=request.user.username  # 存目前登入者的名字
            )
            return redirect('index')  # 发帖成功后，跳回首页（或其他页面）
        else:
            return render(request, 'confession/post.html', {'error': 'Content cannot be empty.'})
    return render(request, 'confession/post.html')

def confession_list_view(request):
    confessions = Confession.objects.filter(is_deleted=False).order_by('-timestamp')  
    return render(request, 'confession/index.html', {'confessions': confessions})

def comment_view(request, confession_id):
    if request.method == "POST":
        confession = get_object_or_404(Confession, id=confession_id)
        content = request.POST.get('content')
        user = request.user.username if request.user.is_authenticated else "Anonymous"

        Comment.objects.create(
            confession=confession,
            content=content,
            user=user
        )
        return redirect('full_post', confession_id=confession_id)
    else:
        return redirect('full_post', confession_id=confession_id)
    
def full_post_view(request, confession_id):
    confession = get_object_or_404(Confession, id=confession_id)
    comments = Comment.objects.filter(confession=confession).order_by('-timestamp')
    return render(request, 'confession/full_post.html', {'confession': confession, 'comments': comments})

def upvote_confession(request, confession_id):
    confession = get_object_or_404(Confession, id=confession_id)
    confession.upvotes += 1
    confession.save()
    return redirect('full_post', confession_id=confession.id)

def trending_view(request):
    confessions = Confession.objects.filter(is_deleted=False).order_by('-upvotes', '-timestamp')
    return render(request, 'confession/trending.html', {'confessions': confessions})

def search_view(request):
    query = request.GET.get('q')
    results = []
    if query:
        results = Confession.objects.filter(
            Q(content__icontains=query),
            is_deleted=False
        ).order_by('-timestamp')
    return render(request, 'confession/search_results.html', {'confessions': results, 'query': query})