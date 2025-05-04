from django.http import JsonResponse
from .models import Notification
from django.views.decorators.http import require_GET

@require_GET
def notification_list(request):
    if not request.session.session_key:
        return JsonResponse({'error': 'Session required'}, status=401)
    
    notifications = Notification.objects.filter(
        recipient_key=request.session.session_key
    ).select_related('post', 'comment', 'reply')[:50]
    
    data = [{
        'type': n.notification_type,
        'message': n.get_message(),
        'is_read': n.is_read,
        'timestamp': n.created_at.isoformat(),
        'post_id': n.post.id if n.post else None,
        'comment_id': n.comment.id if n.comment else None
    } for n in notifications]
    
    return JsonResponse({'notifications': data})

@require_GET
def mark_as_read(request, notification_id):
    Notification.objects.filter(
        id=notification_id,
        recipient_key=request.session.session_key
    ).update(is_read=True)
    return JsonResponse({'status': 'success'})