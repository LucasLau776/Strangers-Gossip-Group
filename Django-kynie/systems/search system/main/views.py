# main/views.py
from django.shortcuts import render
from .models import Post
from django.db.models import Q

def home(request):
    query = request.GET.get('q', '')
    results = []
    
    if query:
        results = Post.objects.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query)
        )
    
    return render(request, 'index.html', {
        'results': results,
        'query': query
    })