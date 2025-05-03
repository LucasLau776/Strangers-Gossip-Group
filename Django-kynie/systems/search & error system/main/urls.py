from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='home'),
    path('search/', views.search_view, name='search'),  # keep your search system
    path('trending/', views.trending_view, name='trending'),
    path('post/', views.post_view, name='post'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('notification/', views.notification_view, name='notification'),
    path('bookmark/', views.bookmark_view, name='bookmark'),
    path('post/<int:post_id>/', views.full_post_view, name='full_post'),

]
