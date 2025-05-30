from django.db import models
from core.models import User
from django.utils import timezone

class Post(models.Model):
    POST_TYPES = [
        ('track', 'Track'),
        ('album', 'Album'),
        ('rating', 'Rating'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post_type = models.CharField(max_length=10, choices=POST_TYPES)
    content = models.TextField(blank=True)
    spotify_id = models.CharField(max_length=100)
    spotify_name = models.CharField(max_length=255)
    spotify_artist = models.CharField(max_length=255)
    spotify_image_url = models.URLField(blank=True)
    spotify_preview_url = models.URLField(blank=True, null=True)
    spotify_url = models.URLField()
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.spotify_name}"
    
    def get_spotify_uri(self):
        """Get the Spotify URI for the track/album"""
        if self.post_type == 'track':
            return f"spotify:track:{self.spotify_id}"
        elif self.post_type == 'album':
            return f"spotify:album:{self.spotify_id}"
        return None
    
    def get_like_count(self):
        """Get the number of likes for this post"""
        return self.likes.count()
    
    def get_comment_count(self):
        """Get the number of comments for this post"""
        return self.comments.count()
    
    def is_liked_by(self, user):
        """Check if a user has liked this post"""
        if user.is_authenticated:
            return self.likes.filter(user=user).exists()
        return False


class Like(models.Model):
    """Model to track post likes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='likes', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} likes {self.post.spotify_name}"


class Comment(models.Model):
    """Model to track post comments with threading support"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}..."
    
    def get_reply_count(self):
        """Get the number of replies to this comment"""
        return self.replies.count()
    
    def is_reply(self):
        """Check if this comment is a reply to another comment"""
        return self.parent is not None


class Follow(models.Model):
    """Model to track follower/following relationships"""
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('follower', 'following')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
