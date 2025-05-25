from django.urls import path
from . import views
from confession import views


urlpatterns = [
    path('', views.home, name='home'),
    path('post/', views.post_confession, name='post_confession'),  # ✔️ 确保这个有
    path('submit_post/', views.submit_post_view, name='submit_post'),  # ✔️ AJAX 或表单提交用
    path('login/', views.login_view, name='login'),  # ✔️ 登录页面
    path('register/', views.register_view, name='register'),  # ✔️ 注册页面
    path('trending/', views.trending_view, name='trending'),  # ✔️ Trending 页面
    path('post/<int:post_id>/', views.full_post, name='full_post'),
    path('save_post/<int:post_id>/', views.toggle_save_post, name='save_post'),
    path('unsave_post/', views.unsave_post, name='unsave_post'),
    path('toggle_save_post/<int:post_id>/', views.toggle_save_post, name='toggle_save_post'),

    # Ajax APIs
    path('like_post/', views.like_post, name='like_post'),
    path('like_comment/', views.like_comment, name='like_comment'),
    path('like_reply/', views.like_reply, name='like_reply'),
    path('add_comment/', views.add_comment, name='add_comment'),
    path('add_reply/', views.add_reply, name='add_reply'),
    path('submit_post/', views.submit_post_view, name='submit_post'),
    path('search/', views.search_view, name='search'),
    path('trending/', views.trending_view, name='trending'),
    path('report_comment/<int:comment_id>/', views.report_view, name='report_comment'),
    path('bookmark/', views.bookmark_view, name='bookmark'),
    path('notifications/', views.get_notifications, name='notifications'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('post/<int:post_id>/save/', views.toggle_save_post, name='save_post'),
    path('<str:content_type>/<int:object_id>/report/', views.report_view, name='report_post'),
    path('confession/<str:content_type>/<int:object_id>/report/', views.report_view, name='report_post'),
    path('done_report/', views.done_report_view, name='done_report'),

]
