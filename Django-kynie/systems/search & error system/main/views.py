from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .models import Post
from django.db.models import Q, Count
from django.utils.timezone import now

def index_view(request):
    query = request.GET.get('q', '')
    results = []

    if query:
        results = Post.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        )
    else:
        results = Post.objects.all()[:10]

    return render(request, 'index.html', {
        'results': results,
        'query': query
    })

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

def search_view(request):
    query = request.GET.get('q', '')
    filter_type = request.GET.get('filter', 'date')
    results = Post.objects.all()

    if query:
        results = results.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        )

    if filter_type == 'date':
        results = results.order_by('-created_at')
    elif filter_type == 'year':
        results = results.filter(created_at__year=now().year).order_by('-created_at')
    elif filter_type == 'popularity':
        results = results.annotate(like_count=Count('likes')).order_by('-like_count')

    return render(request, 'main/search.html', {
        'results': results,
        'query': query,
        'filter': filter_type
    })

def full_post_view(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return render(request, '404.html', status=404)

    return render(request, 'full_post.html', {
        'post': post
    })

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)

def broken_view(request):
    raise Exception("Intentional error to test 500 page")

def test_error(request):
    raise Exception("Intentional 500 error")

def trigger_error(request):
    raise Exception("Test 500 Error")