from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # Removed separate search URL as we're handling search on home
]