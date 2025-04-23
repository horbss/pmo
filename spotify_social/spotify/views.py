from django.shortcuts import render, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models import User
from .models import TrackRating
from social.models import Post
import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)

# Create your views here.

def spotify_login(request):
    """Redirect to Spotify authorization page"""
    logger.debug(f"Client ID: {settings.SPOTIFY_CLIENT_ID}")
    logger.debug(f"Client Secret: {settings.SPOTIFY_CLIENT_SECRET}")
    logger.debug(f"Redirect URI: {settings.SPOTIFY_REDIRECT_URI}")
    logger.debug(f"Scopes: {settings.SPOTIFY_SCOPES}")
    
    try:
        sp_oauth = SpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI,
            scope=settings.SPOTIFY_SCOPES
        )
        auth_url = sp_oauth.get_authorize_url()
        logger.debug(f"Generated auth URL: {auth_url}")
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Error in spotify_login: {str(e)}")
        messages.error(request, 'Error connecting to Spotify. Please try again.')
        return redirect('home')

def spotify_callback(request):
    """Handle Spotify OAuth callback"""
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope=settings.SPOTIFY_SCOPES
    )
    
    try:
        token_info = sp_oauth.get_access_token(request.GET.get('code'))
        if token_info:
            # Get Spotify user data
            sp = spotipy.Spotify(auth=token_info['access_token'])
            spotify_user = sp.current_user()
            
            # Debug log the Spotify user data
            logger.debug(f"Spotify user data: {spotify_user}")
            
            # Check if user already exists with this Spotify email
            try:
                user = User.objects.get(email=spotify_user['email'])
                # Update their Spotify token and ID
                user.spotify_access_token = token_info['access_token']
                user.spotify_refresh_token = token_info.get('refresh_token')
                user.spotify_id = spotify_user['id']  # Save the Spotify ID
                user.save()
                login(request, user)
                messages.success(request, 'Successfully logged in with Spotify!')
            except User.DoesNotExist:
                # Create new user with Spotify display name as username
                username = spotify_user['display_name'].lower().replace(' ', '_')
                # Ensure username is unique
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=spotify_user['email'],
                    spotify_access_token=token_info['access_token'],
                    spotify_refresh_token=token_info.get('refresh_token'),
                    spotify_id=spotify_user['id']  # Save the Spotify ID
                )
                login(request, user)
                messages.success(request, 'Account created successfully! You can update your username in your profile.')
            
            return redirect('profile')
    
    except Exception as e:
        logger.error(f"Error in Spotify callback: {str(e)}")
        messages.error(request, 'Error connecting to Spotify. Please try again.')
        return redirect('home')

@login_required
def spotify_disconnect(request):
    """Disconnect Spotify account"""
    request.user.spotify_access_token = None
    request.user.spotify_refresh_token = None
    request.user.save()
    
    messages.success(request, 'Successfully disconnected from Spotify.')
    return redirect('profile')

@login_required
def spotify_search(request):
    """Search for tracks and albums on Spotify"""
    if not request.user.spotify_access_token:
        messages.error(request, 'Please connect your Spotify account first.')
        return redirect('profile')
    
    query = request.GET.get('q', '')
    results = {'tracks': [], 'albums': []}
    
    if query:
        try:
            sp = spotipy.Spotify(auth=request.user.spotify_access_token)
            
            # Search for tracks
            track_results = sp.search(q=query, type='track', limit=10)
            tracks = track_results['tracks']['items']
            
            # Get user ratings for tracks
            track_ids = [track['id'] for track in tracks]
            user_ratings = {
                rating.track_id: rating.rating 
                for rating in TrackRating.objects.filter(
                    user=request.user, 
                    track_id__in=track_ids
                )
            }
            
            # Get average ratings for tracks
            avg_ratings = {
                track_id: TrackRating.get_average_rating(track_id)
                for track_id in track_ids
            }
            
            # Add ratings to track data
            for track in tracks:
                track['user_rating'] = user_ratings.get(track['id'])
                track['spotify_url'] = track['external_urls']['spotify']
                track['preview_url'] = track['preview_url']
                track['avg_rating'] = avg_ratings.get(track['id'], {'average': None, 'count': 0})
            
            results['tracks'] = tracks
            
            # Search for albums
            album_results = sp.search(q=query, type='album', limit=10)
            albums = album_results['albums']['items']
            
            # Add Spotify URLs to albums
            for album in albums:
                album['spotify_url'] = album['external_urls']['spotify']
            
            results['albums'] = albums
            
        except Exception as e:
            messages.error(request, 'Error searching Spotify. Please try again.')
            logger.error(f"Spotify search error: {str(e)}")
    
    return render(request, 'spotify/search_results.html', {
        'query': query,
        'results': results
    })

@login_required
def rate_track(request):
    """Handle track rating submission"""
    if request.method == 'POST':
        track_id = request.POST.get('track_id')
        track_name = request.POST.get('track_name')
        artist_name = request.POST.get('artist_name')
        rating = int(request.POST.get('rating'))
        
        try:
            # Update or create rating
            rating_obj, created = TrackRating.objects.update_or_create(
                user=request.user,
                track_id=track_id,
                defaults={
                    'track_name': track_name,
                    'artist_name': artist_name,
                    'rating': rating
                }
            )
            
            # Create a post about the rating
            sp = spotipy.Spotify(auth=request.user.spotify_access_token)
            track = sp.track(track_id)
            
            Post.objects.create(
                user=request.user,
                post_type='rating',
                content=f"Rated this song {rating}/5 stars!",
                spotify_id=track_id,
                spotify_name=track_name,
                spotify_artist=artist_name,
                spotify_image_url=track['album']['images'][0]['url'] if track['album']['images'] else '',
                spotify_preview_url=track['preview_url'],
                spotify_url=track['external_urls']['spotify']
            )
            
            return JsonResponse({
                'success': True,
                'rating': rating,
                'message': 'Rating saved successfully'
            })
            
        except Exception as e:
            logger.error(f"Error saving rating: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Error saving rating'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)
