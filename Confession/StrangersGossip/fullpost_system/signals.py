# signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import SessionIdentity

@receiver(user_logged_in)
def bind_session_to_user(sender, request, user, **kwargs):
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    SessionIdentity.objects.update_or_create(
        user=user,
        defaults={'session_key': session_key}
    )
