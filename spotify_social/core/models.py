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
    
    def __str__(self):
        return self.username
