from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Confession, Comment

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
