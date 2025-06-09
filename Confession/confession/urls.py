from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from .views import moderation_panel, moderation_dismiss_user

urlpatterns = [
    path('', views.home, name='home'),
    path('post/', views.post, name='post_confession'),  
    path('submit_post/', views.submit_post_view, name='submit_post'),

    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('trending/', views.trending_view, name='trending'),
    path('post/<int:post_id>/', views.full_post, name='full_post'),

    path('profile/', views.profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),

    # Ajax APIs
    path('like_post/', views.like_post, name='like_post'),
    path('like_comment/', views.like_comment, name='like_comment'),
    path('like_reply/', views.like_reply, name='like_reply'),

    path('add_comment/', views.add_comment, name='add_comment'),
    path('add_reply/', views.add_reply, name='add_reply'),

    path('search/', views.search_view, name='search'),
    
    path('post/delete/<int:post_id>/', views.delete_post, name='delete_post'),
    path('comment/delete/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('reply/delete/<int:reply_id>/', views.delete_reply, name='delete_reply'),

    path('report_comment/<int:comment_id>/', views.report_view, name='report_comment'),
    path('<str:content_type>/<int:object_id>/report/', views.report_view, name='report_post'),
    path('done_report/', views.done_report_view, name='done_report'),

    path('bookmark/', views.bookmark_view, name='bookmark'),

    path('notifications/', views.get_notifications, name='notifications'),
    path('notifications/<int:notification_id>/mark_as_read/', views.mark_as_read, name='mark_as_read'),

    path('toggle_save_post/<int:post_id>/', views.toggle_save_post, name='toggle_save_post'),
    path('unsave_post/', views.unsave_post, name='unsave_post'),

   
    path('ajax_post_confession/', views.ajax_post_confession, name='ajax_post_confession'),

    path('load_replies/<int:comment_id>/', views.load_replies, name='load_replies'),
   
    path('moderation/', moderation_panel, name='moderation_panel'),
    path('moderation/delete/<str:content_type>/<int:object_id>/', views.moderation_delete, name='moderation_delete'),
    path('moderation/dismiss/<str:content_type>/<int:object_id>/', views.moderation_dismiss, name='moderation_dismiss'),
    path('moderation/warn/<int:user_id>/', views.moderation_warn, name='moderation_warn'),
    path('moderation/ban/<int:user_id>/', views.moderation_ban, name='moderation_ban'),
    path('moderation/unban/<int:user_id>/', views.moderation_unban, name='moderation_unban'),
    path('moderation/dismiss/user/<int:user_id>/', views.moderation_dismiss_user, name='moderation_dismiss_user'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)