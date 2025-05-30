from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Post, Follow
from core.models import User
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import re
from django.utils import timezone
from django.db.models import Q

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
    is_private = request.POST.get('is_private') == 'true'
    
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
                rating=rating if rating else None,
                is_private=is_private
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

@login_required
@require_POST
def add_to_listen_later(request):
    """Add a track to the user's Listen Later playlist"""
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
        
        # Verify the track exists
        try:
            track_info = sp.track(spotify_uri.split(':')[-1])
            if not track_info:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid track'
                })
        except Exception as e:
            logger.error(f"Error verifying track: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Invalid track'
            })
        
        # Check if track is already in playlist
        try:
            playlist_tracks = sp.playlist_items(request.user.listen_later)
            for item in playlist_tracks['items']:
                if item['track']['uri'] == spotify_uri:
                    return JsonResponse({
                        'success': False,
                        'message': 'Track is already in your Listen Later playlist'
                    })
        except Exception as e:
            logger.error(f"Error checking playlist: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Error checking playlist'
            })
        
        # Add to playlist
        try:
            sp.playlist_add_items(
                playlist_id=request.user.listen_later,
                items=[spotify_uri]
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Track added to Listen Later playlist!'
            })
        except Exception as e:
            logger.error(f"Error adding to playlist: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Error adding to playlist'
            })
            
    except Exception as e:
        logger.error(f"Error in add_to_listen_later: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error adding to Listen Later playlist'
        })

@login_required
@require_POST
def delete_post(request, post_id):
    """Delete a post"""
    try:
        post = get_object_or_404(Post, id=post_id)
        
        # Check if the user owns the post
        if post.user != request.user:
            return JsonResponse({
                'success': False,
                'message': 'You can only delete your own posts.'
            })
        
        post.delete()
        return JsonResponse({
            'success': True,
            'message': 'Post deleted successfully.'
        })
        
    except Exception as e:
        logger.error(f"Error deleting post: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error deleting post: {str(e)}'
        })

@login_required
def edit_post(request, post_id):
    """Edit a post"""
    try:
        post = get_object_or_404(Post, id=post_id)
        
        # Check if the user owns the post
        if post.user != request.user:
            return JsonResponse({
                'success': False,
                'message': 'You can only edit your own posts.'
            })
        
        if request.method == 'GET':
            # Return post data for editing
            return JsonResponse({
                'success': True,
                'post': {
                    'id': post.id,
                    'content': post.content,
                    'rating': float(post.rating) if post.rating else None,
                    'is_private': post.is_private,
                    'spotify_name': post.spotify_name,
                    'spotify_artist': post.spotify_artist,
                    'spotify_image_url': post.spotify_image_url,
                    'post_type': post.post_type
                }
            })
        
        elif request.method == 'POST':
            # Update post
            content = request.POST.get('content', '').strip()
            rating = request.POST.get('rating')
            is_private = request.POST.get('is_private') == 'true'
            
            # Update fields
            post.content = content
            post.is_private = is_private
            
            # Only update rating if provided and valid
            if rating:
                try:
                    rating_float = float(rating)
                    if 1.0 <= rating_float <= 10.0:
                        post.rating = rating_float
                    else:
                        return JsonResponse({
                            'success': False,
                            'message': 'Rating must be between 1.0 and 10.0'
                        })
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid rating value'
                    })
            
            post.save()
            
            # Update track rating if it's a track post with rating
            if rating and post.post_type == 'track':
                try:
                    from spotify.models import TrackRating
                    TrackRating.objects.update_or_create(
                        user=request.user,
                        track_id=post.spotify_id,
                        defaults={
                            'track_name': post.spotify_name,
                            'artist_name': post.spotify_artist,
                            'rating': rating
                        }
                    )
                    logger.info(f"Updated track rating for {post.spotify_id} to {rating}")
                except Exception as rating_error:
                    logger.error(f"Error updating track rating: {str(rating_error)}")
                    # Continue even if rating update fails
            
            return JsonResponse({
                'success': True,
                'message': 'Post updated successfully!'
            })
            
    except Exception as e:
        logger.error(f"Error editing post: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error editing post: {str(e)}'
        })

# Follow System Views

@login_required
def discover_users(request):
    """Discover users to follow"""
    # Get users that the current user is not following and exclude themselves
    following_ids = request.user.following.values_list('following_id', flat=True)
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    
    if search_query:
        # When searching, show ALL users (except self) that match the search
        users_to_discover = User.objects.exclude(id=request.user.id).filter(
            Q(username__icontains=search_query) | 
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query)
        ).order_by('username')
    else:
        # When not searching, show users not currently following (and have Spotify connected)
        users_to_discover = User.objects.exclude(
            Q(id=request.user.id) | Q(id__in=following_ids)
        ).filter(spotify_access_token__isnull=False).order_by('username')
    
    # Add a flag to indicate if each user is already being followed
    for user in users_to_discover:
        user.is_already_following = request.user.is_following(user)
    
    return render(request, 'social/discover_users.html', {
        'users': users_to_discover,
        'search_query': search_query
    })

@login_required
@require_POST 
def follow_user(request, user_id):
    """Follow a user"""
    try:
        user_to_follow = get_object_or_404(User, id=user_id)
        
        # Can't follow yourself
        if user_to_follow == request.user:
            return JsonResponse({
                'success': False,
                'message': 'You cannot follow yourself.'
            })
        
        # Check if already following
        if request.user.is_following(user_to_follow):
            return JsonResponse({
                'success': False,
                'message': f'You are already following {user_to_follow.username}.'
            })
        
        # Create follow relationship
        Follow.objects.create(
            follower=request.user,
            following=user_to_follow
        )
        
        return JsonResponse({
            'success': True,
            'message': f'You are now following {user_to_follow.username}!'
        })
        
    except Exception as e:
        logger.error(f"Error following user: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error following user.'
        })

@login_required
@require_POST
def unfollow_user(request, user_id):
    """Unfollow a user"""
    try:
        user_to_unfollow = get_object_or_404(User, id=user_id)
        
        # Check if following
        follow_relation = Follow.objects.filter(
            follower=request.user,
            following=user_to_unfollow
        ).first()
        
        if not follow_relation:
            return JsonResponse({
                'success': False,
                'message': f'You are not following {user_to_unfollow.username}.'
            })
        
        # Delete follow relationship
        follow_relation.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'You have unfollowed {user_to_unfollow.username}.'
        })
        
    except Exception as e:
        logger.error(f"Error unfollowing user: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error unfollowing user.'
        })

@login_required
def feed(request):
    """Display posts from users you follow"""
    # Get users the current user is following
    following_users = request.user.get_following_users()
    
    # Get posts from followed users, excluding private posts
    if following_users.exists():
        feed_posts = Post.objects.filter(
            user__in=following_users,
            is_private=False
        ).order_by('-created_at')
    else:
        feed_posts = Post.objects.none()
    
    return render(request, 'social/feed.html', {
        'posts': feed_posts
    })

@login_required
def following_list(request, user_id=None):
    """Display list of users that a user is following"""
    if user_id:
        profile_user = get_object_or_404(User, id=user_id)
    else:
        profile_user = request.user
    
    following_users = profile_user.get_following_users()
    
    # Add follow status for each following user
    for user in following_users:
        user.is_followed_by_current_user = request.user.is_following(user)
    
    return render(request, 'social/following_list.html', {
        'profile_user': profile_user,
        'following_users': following_users,
        'is_own_profile': profile_user == request.user
    })

@login_required
def followers_list(request, user_id=None):
    """Display list of followers for a user"""
    if user_id:
        profile_user = get_object_or_404(User, id=user_id)
    else:
        profile_user = request.user
    
    followers_users = profile_user.get_followers_users()
    
    # Add follow status for each follower
    for user in followers_users:
        user.is_followed_by_current_user = request.user.is_following(user)
    
    return render(request, 'social/followers_list.html', {
        'profile_user': profile_user,
        'followers_users': followers_users,
        'is_own_profile': profile_user == request.user
    })

@login_required
def user_profile(request, user_id):
    """Display another user's profile"""
    profile_user = get_object_or_404(User, id=user_id)
    
    # Don't show profile for yourself - redirect to main profile
    if profile_user == request.user:
        return redirect('profile')
    
    # Get user's posts - only show public posts if viewing someone else's profile
    if profile_user == request.user:
        # Show all posts if it's the user's own profile
        posts = Post.objects.filter(user=profile_user).order_by('-created_at')
    else:
        # Only show public posts for other users
        posts = Post.objects.filter(user=profile_user, is_private=False).order_by('-created_at')
    
    # Check if current user is following this profile user
    is_following = request.user.is_following(profile_user)
    
    spotify_data = None
    if profile_user.spotify_access_token:
        try:
            # Create SpotifyOAuth instance for token refresh
            sp_oauth = SpotifyOAuth(
                client_id=settings.SPOTIFY_CLIENT_ID,
                client_secret=settings.SPOTIFY_CLIENT_SECRET,
                redirect_uri=settings.SPOTIFY_REDIRECT_URI,
                scope=settings.SPOTIFY_SCOPES
            )
            
            # Try to refresh the token if refresh token exists
            if profile_user.spotify_refresh_token:
                try:
                    token_info = sp_oauth.refresh_access_token(profile_user.spotify_refresh_token)
                    if token_info:
                        profile_user.spotify_access_token = token_info['access_token']
                        profile_user.save()
                        logger.info(f"Refreshed access token for user {profile_user.username}")
                except Exception as refresh_error:
                    logger.error(f"Token refresh failed for {profile_user.username}: {str(refresh_error)}")
            
            sp = spotipy.Spotify(auth=profile_user.spotify_access_token)
            spotify_data = sp.current_user()
        except Exception as e:
            logger.error(f"Error fetching Spotify data for user {profile_user.username}: {str(e)}")
    
    return render(request, 'social/user_profile.html', {
        'profile_user': profile_user,
        'posts': posts,
        'is_following': is_following,
        'spotify_data': spotify_data
    })
