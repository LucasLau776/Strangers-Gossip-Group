from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.urls import reverse
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from .models import Post, Comment, Reply, PostLike, CommentLike, ReplyLike, Report, Confession, Save, Notification, UserProfile
from django.db.models import Count
from datetime import datetime
from .forms import PostForm, MMURegisterForm, MMUAuthenticationForm, ProfileForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
import json

# Basic views
def home(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'confession/index.html', {'posts': posts})

def post(request):
    return render(request, 'confession/post.html')

def notifications(request):
    return render(request, 'confession/notifications.html')

# Auth views
def register_view(request):
    next_url = request.GET.get('next', '')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = 'home'
        
    # If user is already authenticated, redirect to next_url
    if request.user.is_authenticated:
        return redirect(next_url)
        
    if request.method == 'POST':
        form = MMURegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(next_url)
    else:
        # Check if email is already registered
        email = request.GET.get('email')
        if email:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'This email is already registered. Please login.')
                return redirect(f"{reverse('login')}?next={next_url}")
        form = MMURegisterForm()

    return render(request, 'confession/register.html', {
        'form': form,
        'next': next_url
    })

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    next_url = request.GET.get('next', 'home')
    
    if request.method == 'POST':
        form = MMUAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(next_url)
        else:
            messages.error(request, form.error_messages['invalid_login'])
            return redirect(f"{reverse('register')}?next={next_url}")
    else:
        form = MMUAuthenticationForm(request)
    
    return render(request, 'confession/login.html', {
        'form': form,
        'next': next_url
    })

def logout_view(request):
    logout(request)
    return redirect('login')

# Posting views
@login_required(login_url='/login/')
def submit_post_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.session_key = request.session.session_key
            post.save()
            messages.success(request, 'Your post has been submitted!')
            return redirect('home')
    else:
        form = PostForm()
    
    return render(request, 'confession/post.html', {
        'form': form,
        'user': request.user
    })

def full_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post, parent=None).order_by('-created_at')

    is_authenticated = request.user.is_authenticated
    session_key = request.session.session_key or "anonymous"
    
    post_avatar = 'default_avatar.png'
    if request.user.is_authenticated:
        try:
            post_avatar = request.user.userprofile.avatar
        except:
            pass

    is_saved = False
    if is_authenticated:
        is_saved = Save.objects.filter(post=post, session_key=session_key).exists()

    post.views += 1
    post.save()
    
    return render(request, 'confession/full_post.html', {
        'post': post,
        'post_avatar': post_avatar,
        'comments': comments,
        'is_saved': is_saved,
        'user_is_authenticated': is_authenticated,
        'current_user_session_key': session_key,
    })
    
def post_confession(request):
    return render(request, 'confession/post_confession.html')

# Trending and Search
def trending_view(request):
    trending_posts = Post.objects.annotate(
        like_count=Count('likes')
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

# Profile views
@login_required
def profile(request):
    user = request.user
    user_profile = get_object_or_404(UserProfile, user=user)
    context = {
        'user': user,
        'profile': user_profile,
    }
    return render(request, 'confession/profile.html', context)

@login_required
def edit_profile(request):
    user = request.user
    user_profile = get_object_or_404(UserProfile, user=user)
    
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = request.POST
        files = request.FILES
        response_data = {'success': False}

        try:
            if 'avatar' in files:
                if user_profile.avatar and os.path.exists(user_profile.avatar.path):
                    os.remove(user_profile.avatar.path)
 
                user_profile.avatar = files['avatar']
                user_profile.save()
            
            response_data['success'] = True
            response_data['avatar_url'] = user_profile.avatar.url
            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    avatar_choices = [f"avatar{i}.png" for i in range(1, 29)]
    return render(request, 'confession/edit_profile.html', {
        'avatar_choices': avatar_choices,
        'profile': user_profile,
        'user': user,
    })

# AJAX Profile Updates
@login_required
@require_POST
@csrf_exempt
def update_password(request):
    current_password = request.POST.get('current_password', '')
    new_password = request.POST.get('new_password', '')
    confirm_password = request.POST.get('confirm_password', '')
    
    if not request.user.check_password(current_password):
        return JsonResponse({'success': False, 'error': 'Current password is incorrect'})
        
    if new_password != confirm_password:
        return JsonResponse({'success': False, 'error': 'Passwords do not match'})
        
    if len(new_password) < 8:
        return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters'})
        
    request.user.set_password(new_password)
    request.user.save()
    update_session_auth_hash(request, request.user)  # Prevent logout
    return JsonResponse({'success': True})

@login_required
@require_POST
@csrf_exempt
def update_avatar(request):
    avatar = request.POST.get('avatar', '')
    valid_avatars = [f'avatar{i}.png' for i in range(1, 29)]
    
    if avatar not in valid_avatars:
        return JsonResponse({'success': False, 'error': 'Invalid avatar selection'})
        
    profile = get_object_or_404(UserProfile, user=request.user)
    profile.avatar = avatar
    profile.save()
    return JsonResponse({'success': True, 'avatar_url': profile.avatar.url})

@login_required
@require_POST
@csrf_exempt
def update_theme(request):
    dark_mode = request.POST.get('dark_mode', 'false') == 'true'
    profile = get_object_or_404(UserProfile, user=request.user)
    profile.dark_mode = dark_mode
    profile.save()
    return JsonResponse({'success': True})

# AJAX Content Interaction Views
@login_required
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

@login_required
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

@login_required
@require_POST
@csrf_exempt
def add_reply(request):
    comment_id = request.POST.get('comment_id')
    content = request.POST.get('content')
    session_key = request.session.session_key or "anonymous"
    image = request.FILES.get('image', None)
    is_gif = image.name.lower().endswith('.gif') if image else False

    if not comment_id or not content:
        return JsonResponse({'success': False, 'error': 'Missing data'}, status=400)

    try:
        comment = get_object_or_404(Comment, id=comment_id)
        Reply.objects.create(
            comment=comment,
            content=content,
            session_key=session_key,
            user=request.user if request.user.is_authenticated else None,
            image=image,
            is_gif=is_gif
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
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

@login_required
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

@login_required
@require_POST
@csrf_exempt
def like_confession(request, confession_id):
    confession = get_object_or_404(Confession, id=confession_id)
    confession.upvotes += 1
    confession.save()
    return JsonResponse({'success': True, 'upvotes': confession.upvotes})

# Comment/Reply Management
@login_required
@csrf_exempt
def comment_post(request, confession_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        session_key = request.session.session_key or "anonymous"
        confession = get_object_or_404(Confession, id=confession_id)
        Comment.objects.create(
            content=content,
            session_key=session_key,
            post=None
        )
        return redirect('full_post', post_id=confession_id)
    return JsonResponse({'error': 'Only POST allowed'}, status=400)

@login_required
@csrf_exempt
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    if not (request.user == comment.user or 
            (not comment.user and request.session.session_key == comment.session_key)):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    comment.delete()
    return JsonResponse({'success': True})

@login_required
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

@login_required
@csrf_exempt
def delete_reply(request, reply_id):
    reply = get_object_or_404(Reply, id=reply_id)
    
    if not (request.user == reply.user or 
            (not reply.user and request.session.session_key == reply.session_key)):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    reply.delete()
    return JsonResponse({'success': True})

@login_required
@csrf_exempt
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if not (request.user == post.user or 
            (not post.user and request.session.session_key == post.session_key)):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    post.delete()
    return JsonResponse({'success': True})

# Bookmark/Save functionality
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

@login_required
def bookmark_view(request):
    session_key = request.session.session_key or "anonymous"
    saved_posts = Save.objects.filter(session_key=session_key).select_related('post')
    return render(request, 'confession/bookmark.html', {'saved_posts': saved_posts})

@login_required
@csrf_exempt
@require_POST
def unsave_post(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        post_id = request.POST.get('post_id')
        session_key = request.session.session_key or "anonymous"
        Save.objects.filter(post_id=post_id, session_key=session_key).delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

# Report functionality
@login_required
@csrf_exempt
def report_view(request, content_type, object_id):
    if request.method == 'POST':
        reason = request.POST.get('reason')
        if reason:
            try:
                model_type = ContentType.objects.get(model=content_type)
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

# Notification views
@login_required
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

# Error handlers
def custom_404(request, exception):
    return render(request, 'confession/404.html', status=404)

def custom_500(request):
    return render(request, 'confession/500.html', status=500)