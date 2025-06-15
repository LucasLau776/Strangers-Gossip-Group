from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from confession import views  # Ensure you import views from confession app

urlpatterns = [
    # User registration, login, logout
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Main pages and posting
    path('', views.home, name='index'),
    path('post/', views.submit_post_view, name='submit_post'),
    path('trending/', views.trending_view, name='trending'),
    path('search/', views.search_view, name='search'),

    # Confession detail and comments
    path('confession/<int:post_id>/', views.full_post, name='full_post'),
    path('confession/<int:confession_id>/comment/', views.comment_post, name='comment'),
    path('confession/<int:confession_id>/like/', views.like_confession, name='like_confession'),

    # Comments and likes
    path('comment/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('report/<str:content_type>/<int:object_id>/', views.report_view, name='report_content'),

    # Replies, likes and deletes
    path('reply/comment/<int:comment_id>/', views.reply_comment, name='reply_comment'),
    path('reply/<int:reply_id>/like/', views.like_reply, name='like_reply'),
    path('reply/<int:reply_id>/delete/', views.delete_reply, name='delete_reply'),

    # Save and bookmark features
    path('post/<int:post_id>/save/', views.toggle_save_post, name='toggle_save_post'),
    path('post/<int:post_id>/report/', views.report_view, name='report_post'),  
    path('bookmark/', views.bookmark_view, name='bookmark_page'),

    # Report features
    path('report/<str:content_type>/<int:object_id>/', views.report_view, name='report_content'),
    path('report/done/', views.done_report_view, name='done_report'),

    # Notifications
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/<int:notification_id>/mark_as_read/', views.mark_as_read, name='mark_as_read'),

    # Admin site
    path('admin/', admin.site.urls),

    # Include all other confession app URLs
    path('confession/', include('confession.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'confession.views.custom_404'
handler500 = 'confession.views.custom_500'
