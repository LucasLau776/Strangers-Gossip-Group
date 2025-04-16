from django.urls import path
from .views import ConfessionListCreateView, LikeCreateView, CommentCreateView

urlpatterns = [
    path('confessions/', ConfessionListCreateView.as_view(), name='confession-list-create'),
    path('like/', LikeCreateView.as_view(), name='like-create'),
    path('comment/', CommentCreateView.as_view(), name='comment-create'),
]
