from django.urls import path
from . import views

urlpatterns = [
    path('', views.confession_list_view, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('confession/<int:confession_id>/', views.full_post_view, name='full_post'),
    path('confession/<int:confession_id>/comment/', views.comment_view, name='comment'),
    path('confession/<int:confession_id>/like/', views.like_confession, name='like_confession'),
    path('post/', views.post_confession, name='post_confession'),
    path('trending/', views.trending_view, name='trending'),
    path('search/', views.search_view, name='search'),
    path('comment/<int:comment_id>/like/', views.like_comment, name='like_comment'),

]
