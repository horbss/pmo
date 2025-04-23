"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core import views as core_views
from spotify import views as spotify_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.home, name='home'),
    path('register/', core_views.register, name='register'),
    path('profile/', core_views.profile, name='profile'),
    path('profile/edit-username/', core_views.edit_username, name='edit_username'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    # Spotify authentication URLs
    path('spotify/login/', spotify_views.spotify_login, name='spotify_login'),
    path('spotify/callback/', spotify_views.spotify_callback, name='spotify_callback'),
    path('spotify/disconnect/', spotify_views.spotify_disconnect, name='spotify_disconnect'),
    path('spotify/search/', spotify_views.spotify_search, name='spotify_search'),
    path('spotify/rate/', spotify_views.rate_track, name='rate_track'),
    path('social/', include('social.urls')),
]
