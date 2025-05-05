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
from django.views.decorators.http import require_POST

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
                
                listen_later = sp.user_playlist_create(
                    user=spotify_user['id'],
                    name="listen later",
                    public=True,
                    description="made for pmo"
                )               
                
                user = User.objects.create_user(
                    username=username,
                    email=spotify_user['email'],
                    spotify_access_token=token_info['access_token'],
                    spotify_refresh_token=token_info.get('refresh_token'),
                    spotify_id=spotify_user['id'],
                    listen_later = listen_later['id']
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

def refresh_spotify_token(user):
    """Refresh Spotify access token using refresh token"""
    try:
        sp_oauth = SpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI,
            scope=settings.SPOTIFY_SCOPES
        )
        
        # Create a token info dictionary with the refresh token
        token_info = {
            'access_token': user.spotify_access_token,
            'refresh_token': user.spotify_refresh_token,
            'expires_at': 0  # Force refresh
        }
        
        # Get new token info
        new_token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        
        if new_token_info:
            # Update user's tokens
            user.spotify_access_token = new_token_info['access_token']
            if 'refresh_token' in new_token_info:
                user.spotify_refresh_token = new_token_info['refresh_token']
            user.save()
            return True
        return False
    except Exception as e:
        logger.error(f"Error refreshing Spotify token: {str(e)}")
        return False

@login_required
def spotify_search(request):
    """Search for tracks and albums on Spotify"""
    if not request.user.spotify_access_token:
        return JsonResponse({
            'error': 'Please connect your Spotify account first.'
        }, status=401)
    
    query = request.GET.get('q', '')
    results = {'tracks': [], 'albums': []}
    
    if not query:
        return JsonResponse({
            'error': 'Search query is required.'
        }, status=400)
    
    try:
        # Try to create Spotify client with current token
        try:
            sp = spotipy.Spotify(auth=request.user.spotify_access_token)
            # Test the token by making a simple request
            sp.current_user()
        except Exception as e:
            logger.warning(f"Spotify token expired or invalid: {str(e)}")
            # Try to refresh the token
            if refresh_spotify_token(request.user):
                sp = spotipy.Spotify(auth=request.user.spotify_access_token)
            else:
                return JsonResponse({
                    'error': 'Error fetching Spotify data. Please reconnect your Spotify account.'
                }, status=401)
        
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
            track['avg_rating'] = avg_ratings.get(track['id'], {'average': None, 'count': 0})
        
        results['tracks'] = tracks
        
        # Search for albums
        album_results = sp.search(q=query, type='album', limit=10)
        albums = album_results['albums']['items']
        
        # Add Spotify URLs to albums
        for album in albums:
            album['spotify_url'] = album['external_urls']['spotify']
        
        results['albums'] = albums
        
        return JsonResponse(results)
        
    except Exception as e:
        logger.error(f"Spotify search error: {str(e)}")
        return JsonResponse({
            'error': 'Error searching Spotify. Please try again.'
        }, status=500)

# create a post based on the track rating - we want to remove this . 
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
                post_type='track',  # Changed from 'rating' to 'track' to enable queue functionality
                content=f"Rated this song {rating}/5 stars!",
                spotify_id=track_id,
                spotify_name=track_name,
                spotify_artist=artist_name,
                spotify_image_url=track['album']['images'][0]['url'] if track['album']['images'] else '',
                spotify_preview_url=track['preview_url'],  # This is needed for the queue button
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

@login_required
def get_spotify_token(request):
    """Get Spotify access token for Web Playback SDK"""
    if not request.user.spotify_access_token:
        return JsonResponse({'error': 'Spotify account not connected'}, status=401)
    
    try:
        # Create SpotifyOAuth instance
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
            return JsonResponse({'access_token': token_info['access_token']})
        
        return JsonResponse({'access_token': request.user.spotify_access_token})
    except Exception as e:
        logger.error(f"Error getting Spotify token: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def search_page(request):
    """Render search results page"""
    if not request.user.spotify_access_token:
        messages.error(request, 'Please connect your Spotify account first.')
        return redirect('profile')
    
    query = request.GET.get('q', '')
    if not query:
        return render(request, 'spotify/search.html', {
            'error': 'Search query is required.'
        })
    
    try:
        # Try to create Spotify client with current token
        try:
            sp = spotipy.Spotify(auth=request.user.spotify_access_token)
            # Test the token by making a simple request
            sp.current_user()
        except Exception as e:
            logger.warning(f"Spotify token expired or invalid: {str(e)}")
            # Try to refresh the token
            if refresh_spotify_token(request.user):
                sp = spotipy.Spotify(auth=request.user.spotify_access_token)
            else:
                messages.error(request, 'Error fetching Spotify data. Please reconnect your Spotify account.')
                return redirect('profile')
        
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
            track['avg_rating'] = avg_ratings.get(track['id'], {'average': None, 'count': 0})
        
        # Search for albums
        album_results = sp.search(q=query, type='album', limit=10)
        albums = album_results['albums']['items']
        
        # Add Spotify URLs to albums
        for album in albums:
            album['spotify_url'] = album['external_urls']['spotify']
        
        context = {
            'query': query,
            'tracks': tracks,
            'albums': albums,
        }
        
        return render(request, 'spotify/search.html', context)
    
    except Exception as e:
        logger.error(f"Error in search_page: {str(e)}")
        messages.error(request, 'Error searching Spotify. Please try again.')
        return redirect('profile')

@login_required
def get_top_albums(request):
    if not request.user.spotify_access_token:
        return JsonResponse({'error': 'Spotify not connected'}, status=400)
        
    try:
        sp = spotipy.Spotify(auth=request.user.spotify_access_token)
        
        # Get user's top tracks
        top_tracks = sp.current_user_top_tracks(limit=50, time_range='medium_term')
        
        # Create a dictionary to store unique albums
        albums_dict = {}
        
        # Process each track and extract album information
        for track in top_tracks['items']:
            album = track['album']
            album_id = album['id']
            
            # Only add the album if we haven't seen it before
            if album_id not in albums_dict:
                albums_dict[album_id] = {
                    'id': album_id,
                    'name': album['name'],
                    'artists': album['artists'],
                    'images': album['images'],
                    'spotify_url': album['external_urls']['spotify']
                }
            
            # Stop once we have 3 unique albums
            if len(albums_dict) >= 3:
                break
        
        # Convert dictionary to list
        albums = list(albums_dict.values())
                
        return JsonResponse({'albums': albums})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_POST
def remove_from_playlist(request):
    """Remove a track from the listen later playlist"""
    if not request.user.spotify_access_token:
        return JsonResponse({'success': False, 'message': 'Spotify account not connected'})
    
    track_uri = request.POST.get('track_uri')
    if not track_uri:
        return JsonResponse({'success': False, 'message': 'No track URI provided'})
    
    try:
        sp = spotipy.Spotify(auth=request.user.spotify_access_token)
        
        # Remove the track from the playlist
        sp.playlist_remove_all_occurrences_of_items(
            request.user.listen_later,
            [track_uri]
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Track removed from playlist'
        })
    except Exception as e:
        logger.error(f"Error removing track from playlist: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error removing track from playlist'
        })

@login_required
def get_album_tracks(request, album_id):
    """Get all tracks from an album"""
    if not request.user.spotify_access_token:
        return JsonResponse({
            'error': 'Please connect your Spotify account first.'
        }, status=401)
    
    try:
        # Try to create Spotify client with current token
        try:
            sp = spotipy.Spotify(auth=request.user.spotify_access_token)
            # Test the token by making a simple request
            sp.current_user()
        except Exception as e:
            logger.warning(f"Spotify token expired or invalid: {str(e)}")
            # Try to refresh the token
            if refresh_spotify_token(request.user):
                sp = spotipy.Spotify(auth=request.user.spotify_access_token)
            else:
                return JsonResponse({
                    'error': 'Error fetching Spotify data. Please reconnect your Spotify account.'
                }, status=401)
        
        # Get album tracks
        album_tracks = sp.album_tracks(album_id)
        tracks = album_tracks['items']
        
        # Add Spotify URLs to tracks
        for track in tracks:
            track['spotify_url'] = track['external_urls']['spotify']
        
        return JsonResponse({
            'tracks': tracks
        })
        
    except Exception as e:
        logger.error(f"Error fetching album tracks: {str(e)}")
        return JsonResponse({
            'error': 'Error fetching album tracks. Please try again.'
        }, status=500)
