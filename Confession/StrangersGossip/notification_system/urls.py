from django.urls import path
from notification_system import views

urlpatterns = [
    path('api/notifications/', views.notification_list, name='notification-list'),
    path('api/notifications/<int:notification_id>/read/', 
         views.mark_as_read, name='mark-as-read'),
]