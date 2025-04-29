# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='home'),                        # Home/search page
    path('trending/', views.trending_view, name='trending'),       # Trending page
    path('post/', views.post_view, name='post'),                    # Create new post
    path('login/', views.login_view, name='login'),                 # Login page
    path('register/', views.register_view, name='register'),       # Register page
    path('notification/', views.notification_view, name='notification'),  # Notifications
    path('bookmark/', views.bookmark_view, name='bookmark'),       # Bookmarked posts
]
