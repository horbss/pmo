from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Post
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import re

logger = logging.getLogger(__name__)

@login_required
def create_post(request):
    """Create a new post about a track or album"""
    if not request.user.spotify_access_token:
        messages.error(request, 'Please connect your Spotify account first.')
        return redirect('profile')
    
    if request.method == 'POST':
        spotify_link = request.POST.get('spotify_link')
        content = request.POST.get('content')
        post_type = request.POST.get('post_type')
        
        # Extract ID from Spotify link
        track_match = re.search(r'spotify\.com/track/([a-zA-Z0-9]+)', spotify_link)
        album_match = re.search(r'spotify\.com/album/([a-zA-Z0-9]+)', spotify_link)
        
        if not (track_match or album_match):
            messages.error(request, 'Invalid Spotify link. Please provide a valid track or album link.')
            return redirect('profile')
        
        spotify_id = (track_match or album_match).group(1)
        
        try:
            # Create SpotifyOAuth instance
            sp_oauth = SpotifyOAuth(
                client_id=settings.SPOTIFY_CLIENT_ID,
                client_secret=settings.SPOTIFY_CLIENT_SECRET,
                redirect_uri=settings.SPOTIFY_REDIRECT_URI,
                scope='user-read-private user-read-email'
            )
            
            # Try to refresh the token
            token_info = sp_oauth.refresh_access_token(request.user.spotify_refresh_token)
            if token_info:
                request.user.spotify_access_token = token_info['access_token']
                request.user.save()
            
            # Create Spotify instance with new token
            sp = spotipy.Spotify(auth=request.user.spotify_access_token)
            
            if post_type == 'track':
                track = sp.track(spotify_id)
                post = Post.objects.create(
                    user=request.user,
                    post_type='track',
                    content=content,
                    spotify_id=spotify_id,
                    spotify_name=track['name'],
                    spotify_artist=', '.join([artist['name'] for artist in track['artists']]),
                    spotify_image_url=track['album']['images'][0]['url'] if track['album']['images'] else '',
                    spotify_preview_url=track['preview_url'],
                    spotify_url=track['external_urls']['spotify']
                )
            else:  # album
                album = sp.album(spotify_id)
                post = Post.objects.create(
                    user=request.user,
                    post_type='album',
                    content=content,
                    spotify_id=spotify_id,
                    spotify_name=album['name'],
                    spotify_artist=', '.join([artist['name'] for artist in album['artists']]),
                    spotify_image_url=album['images'][0]['url'] if album['images'] else '',
                    spotify_preview_url=None,
                    spotify_url=album['external_urls']['spotify']
                )
            
            messages.success(request, 'Post created successfully!')
        except Exception as e:
            logger.error(f"Error creating post: {str(e)}")
            messages.error(request, f'Error creating post: {str(e)}')
    
    return redirect('profile')

@login_required
@require_POST
def add_to_queue(request):
    if not request.user.spotify_access_token:
        return JsonResponse({'success': False, 'message': 'Spotify account not connected'})
    
    spotify_uri = request.POST.get('spotify_uri')
    if not spotify_uri:
        return JsonResponse({'success': False, 'message': 'No track URI provided'})
    
    try:
        # Create SpotifyOAuth instance with all required scopes
        sp_oauth = SpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI,
            scope=settings.SPOTIFY_SCOPES
        )
        
        # Try to refresh the token
        token_info = sp_oauth.refresh_access_token(request.user.spotify_refresh_token)
        if token_info:
            request.user.spotify_access_token = token_info['access_token']
            request.user.save()
        
        # Create Spotify instance with new token
        sp = spotipy.Spotify(auth=request.user.spotify_access_token)
        
        # Check if user has an active device
        devices = sp.devices()
        if not devices['devices']:
            return JsonResponse({
                'success': False, 
                'message': 'No active Spotify device found. Please make sure Spotify is open on one of your devices.'
            })
        
        # Check if any device is currently playing
        current_playback = sp.current_playback()
        if not current_playback or not current_playback['is_playing']:
            return JsonResponse({
                'success': False,
                'message': 'No device is currently playing. Please start playback on one of your devices.'
            })
        
        # Get the active device ID
        active_device = next((device for device in devices['devices'] if device['is_active']), None)
        if not active_device:
            return JsonResponse({
                'success': False,
                'message': 'No active device found. Please make sure Spotify is the active device.'
            })
        
        # Add to queue with the active device
        sp.add_to_queue(uri=spotify_uri, device_id=active_device['id'])
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"Error adding to queue: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)})
