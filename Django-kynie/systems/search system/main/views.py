from django.shortcuts import render
from .models import Post
from django.db.models import Q
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

def search_view(request):
    query = request.GET.get('q', '')
    filter_type = request.GET.get('filter', '')
    results = Post.objects.all()

    # Apply search
    if query:
        results = results.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        )

    # Apply filter
    if filter_type == 'date':
        results = results.order_by('-created_at')
    elif filter_type == 'year':
        current_year = now().year
        results = results.filter(created_at__year=current_year).order_by('-created_at')
    elif filter_type == 'popularity':
        # You don’t have a popularity field, so fallback to created date
        results = results.order_by('-created_at')

    return render(request, 'search.html', {
        'results': results,
        'query': query
    })

def full_post_view(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return render(request, '404.html', status=404)

    return render(request, 'full_post.html', {
        'post': post
    })
