from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    spotify_id = models.CharField(max_length=255, blank=True, null=True)
    spotify_access_token = models.CharField(max_length=255, blank=True, null=True)
    spotify_refresh_token = models.CharField(max_length=255, blank=True, null=True)
    
    # Top 3 albums picked by user
    top_album1_id = models.CharField(max_length=255, blank=True, null=True)
    top_album1_name = models.CharField(max_length=255, blank=True, null=True)
    top_album1_image = models.URLField(max_length=500, blank=True, null=True)
    
    top_album2_id = models.CharField(max_length=255, blank=True, null=True)
    top_album2_name = models.CharField(max_length=255, blank=True, null=True)
    top_album2_image = models.URLField(max_length=500, blank=True, null=True)
    
    top_album3_id = models.CharField(max_length=255, blank=True, null=True)
    top_album3_name = models.CharField(max_length=255, blank=True, null=True)
    top_album3_image = models.URLField(max_length=500, blank=True, null=True)
    
    # Top 3 artists picked by user
    top_artist1_id = models.CharField(max_length=255, blank=True, null=True)
    top_artist1_name = models.CharField(max_length=255, blank=True, null=True)
    top_artist1_image = models.URLField(max_length=500, blank=True, null=True)
    
    top_artist2_id = models.CharField(max_length=255, blank=True, null=True)
    top_artist2_name = models.CharField(max_length=255, blank=True, null=True)
    top_artist2_image = models.URLField(max_length=500, blank=True, null=True)
    
    top_artist3_id = models.CharField(max_length=255, blank=True, null=True)
    top_artist3_name = models.CharField(max_length=255, blank=True, null=True)
    top_artist3_image = models.URLField(max_length=500, blank=True, null=True)
    
    listen_later = models.CharField(max_length=255, blank=True, null=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    
    def get_top_albums(self):
        """Return a list of dictionaries containing top album data"""
        albums = []
        for i in range(1, 4):
            album = {
                'id': getattr(self, f'top_album{i}_id'),
                'name': getattr(self, f'top_album{i}_name'),
                'image': getattr(self, f'top_album{i}_image'),
                'position': i
            }
            albums.append(album)
        return albums

    def get_top_artists(self):
        """Return a list of dictionaries containing top artist data"""
        artists = []
        for i in range(1, 4):
            artist = {
                'id': getattr(self, f'top_artist{i}_id'),
                'name': getattr(self, f'top_artist{i}_name'),
                'image': getattr(self, f'top_artist{i}_image'),
                'position': i
            }
            artists.append(artist)
        return artists

    def get_follower_count(self):
        """Return the number of followers"""
        return self.followers.count()

    def get_following_count(self):
        """Return the number of users this user is following"""
        return self.following.count()

    def is_following(self, user):
        """Check if this user is following another user"""
        return self.following.filter(following=user).exists()

    def get_following_users(self):
        """Get all users this user is following"""
        return User.objects.filter(followers__follower=self)

    def get_followers_users(self):
        """Get all users following this user"""
        return User.objects.filter(following__following=self)

    def __str__(self):
        return self.username
