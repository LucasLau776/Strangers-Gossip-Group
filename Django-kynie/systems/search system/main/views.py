from django.shortcuts import render
from .models import Post
from django.db.models import Q
from main import views

def index_view(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        results = Post.objects.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query)
        )
    else:
        results = Post.objects.all()[:10]  # Show latest 10 posts if no query

    return render(request, 'index.html', {
        'results': results,
        'query': query
    })

def home(request):
    return render(request, 'index.html')

def trending_view(request):
    return render(request, 'trending.html')

def post_view(request):
    return render(request, 'post.html')

def login_view(request):
    return render(request, 'login.html')

def register_view(request):
    return render(request, 'register.html')

def notification_view(request):
    return render(request, 'notification.html')

def bookmark_view(request):
    return render(request, 'bookmark.html')
