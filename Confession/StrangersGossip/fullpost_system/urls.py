from django.urls import path
from . import views

urlpatterns = [
    path('post/<int:post_id>/', views.full_post, name='full_post'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('bookmark/', views.bookmark_view, name='bookmark_page'),
    path('post/<int:post_id>/save/', views.toggle_save_post, name='toggle_save_post'),
    path('post/<int:post_id>/report/', views.report_post, name='report_post'),
    path('post/<int:post_id>/comment/', views.comment_post, name='comment_post'),
    path('comment/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    path('reply/comment/<int:comment_id>/', views.reply_comment, name='reply_comment'),
    path('reply/<int:reply_id>/like/', views.like_reply, name='like_reply'),
    path('reply/<int:reply_id>/delete/', views.delete_reply, name='delete_reply'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('report/<str:content_type>/<int:object_id>/', views.report_view, name='report_content'),
    path('report/done/', views.done_report, name='done_report'),
]
