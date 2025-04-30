from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .models import User
from .forms import UsernameEditForm
from social.models import Post
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.http import JsonResponse

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

@login_required
def update_top_album(request):
    if request.method == 'POST':
        position = request.POST.get('position')
        album_id = request.POST.get('album_id')
        album_name = request.POST.get('album_name')
        album_image = request.POST.get('album_image')
        
        if not all([position, album_id, album_name, album_image]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
            
        user = request.user
        if position == '1':
            user.top_album1_id = album_id
            user.top_album1_name = album_name
            user.top_album1_image = album_image
        elif position == '2':
            user.top_album2_id = album_id
            user.top_album2_name = album_name
            user.top_album2_image = album_image
        elif position == '3':
            user.top_album3_id = album_id
            user.top_album3_name = album_name
            user.top_album3_image = album_image
        else:
            return JsonResponse({'error': 'Invalid position'}, status=400)
            
        user.save()
        return JsonResponse({'success': True})
        
    return JsonResponse({'error': 'Invalid request method'}, status=400)
