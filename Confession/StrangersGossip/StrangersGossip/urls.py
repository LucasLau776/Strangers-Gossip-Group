from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('fullpost_system.urls')),
    path('', include('fullpost_system.urls')),
]
