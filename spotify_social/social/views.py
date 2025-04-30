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
from django.utils import timezone

logger = logging.getLogger(__name__)

@login_required
def create_post(request):
    """Create a new post about a track or album"""
    if not request.user.spotify_access_token:
        logger.error("User attempted to create post without Spotify connection")
        return JsonResponse({
            'success': False,
            'message': 'Please connect your Spotify account first.'
        })
    
    if request.method != 'POST':
        logger.error(f"Invalid request method: {request.method}")
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method'
        })
    
    # Check if this is an AJAX request
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        logger.error("Request missing XMLHttpRequest header")
        return JsonResponse({
            'success': False,
            'message': 'Invalid request'
        })
    
    spotify_link = request.POST.get('spotify_link')
    content = request.POST.get('content')
    post_type = request.POST.get('post_type')
    spotify_id = request.POST.get('spotify_id')
    spotify_name = request.POST.get('spotify_name')
    spotify_artist = request.POST.get('spotify_artist')
    spotify_image_url = request.POST.get('spotify_image_url')
    spotify_preview_url = request.POST.get('spotify_preview_url')
    rating = request.POST.get('rating')
    
    # Debug log all POST data
    logger.info(f"Create post request - Type: {post_type}, ID: {spotify_id}, Name: {spotify_name}")
    logger.info(f"Preview URL: {spotify_preview_url}, Image URL: {spotify_image_url}")
    logger.info(f"Content: {content}, Rating: {rating}")
    
    if not spotify_id:
        logger.error("Missing spotify_id in request")
        return JsonResponse({
            'success': False,
            'message': 'Invalid Spotify item. Please try again.'
        })
    
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
            logger.info(f"Refreshed access token for user {request.user.username}")
        
        # Create Spotify instance with new token
        sp = spotipy.Spotify(auth=request.user.spotify_access_token)
        
        # Check if a similar post already exists for this user and track/album
        existing_post = Post.objects.filter(
            user=request.user,
            spotify_id=spotify_id,
            post_type=post_type,
            created_at__gte=timezone.now() - timezone.timedelta(minutes=5)
        ).first()
        
        if existing_post:
            logger.warning(f"Duplicate post attempt for {post_type} {spotify_id} by {request.user.username}")
            return JsonResponse({
                'success': False,
                'message': 'You have already created a post for this item recently.'
            })
        
        # For albums, verify spotify_preview_url handling
        if post_type == 'album' and spotify_preview_url == "":
            # Make sure it's set to None for database storage
            spotify_preview_url = None
            logger.info("Set empty preview URL to None for album post")
        
        # Create the post
        try:
            post = Post.objects.create(
                user=request.user,
                post_type=post_type,
                content=content,
                spotify_id=spotify_id,
                spotify_name=spotify_name,
                spotify_artist=spotify_artist,
                spotify_image_url=spotify_image_url,
                spotify_preview_url=spotify_preview_url,
                spotify_url=spotify_link,
                rating=rating if rating else None
            )
            logger.info(f"Created post {post.id} for {post_type} {spotify_id}")
        except Exception as post_error:
            logger.error(f"Error creating post object: {str(post_error)}")
            return JsonResponse({
                'success': False,
                'message': f'Error creating post: {str(post_error)}'
            })
        
        # If rating is provided and it's a track, create/update the rating
        if rating and post_type == 'track':
            try:
                from spotify.models import TrackRating
                TrackRating.objects.update_or_create(
                    user=request.user,
                    track_id=spotify_id,
                    defaults={
                        'track_name': spotify_name,
                        'artist_name': spotify_artist,
                        'rating': rating
                    }
                )
                logger.info(f"Updated rating for track {spotify_id} to {rating}")
            except Exception as rating_error:
                logger.error(f"Error saving rating: {str(rating_error)}")
                # Continue even if rating fails
        
        return JsonResponse({
            'success': True,
            'message': 'Post created successfully!'
        })
        
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error creating post: {str(e)}'
        })

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
