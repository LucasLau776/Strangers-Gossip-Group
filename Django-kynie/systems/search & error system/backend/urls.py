from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Error handlers
handler404 = 'main.views.custom_404'
handler500 = 'main.views.custom_500'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),  # includes all views, including search
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
