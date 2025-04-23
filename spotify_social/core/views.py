from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .models import User
from .forms import CustomUserCreationForm, UsernameEditForm
from social.models import Post
import spotipy
from spotipy.oauth2 import SpotifyOAuth

def home(request):
    return render(request, 'core/home.html')

@login_required
def profile(request):
    spotify_data = None
    currently_playing = None
    top_artists = None
    top_tracks = None
    
    # Get time range from request, default to medium_term
    time_range = request.GET.get('time_range', 'medium_term')
    
    if request.user.spotify_access_token:
        try:
            sp = spotipy.Spotify(auth=request.user.spotify_access_token)
            spotify_data = sp.current_user()
            
            # Get currently playing track
            current = sp.currently_playing()
            if current and current['is_playing']:
                currently_playing = current['item']
            
            # Get top artists for the selected time range
            top_artists = sp.current_user_top_artists(limit=3, time_range=time_range)
            
            # Get top tracks for the selected time range
            top_tracks = sp.current_user_top_tracks(limit=3, time_range=time_range)
            
        except Exception as e:
            messages.error(request, 'Error fetching Spotify data. Please reconnect your Spotify account.')
    
    # Get user's posts
    posts = Post.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'core/profile.html', {
        'spotify_data': spotify_data,
        'currently_playing': currently_playing,
        'top_artists': top_artists,
        'top_tracks': top_tracks,
        'time_range': time_range,
        'posts': posts
    })

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})

@login_required
def edit_username(request):
    if request.method == 'POST':
        form = UsernameEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your username has been updated successfully!')
            return redirect('profile')
    else:
        form = UsernameEditForm(instance=request.user)
    
    return render(request, 'core/edit_username.html', {
        'form': form
    })
