from django.db import models
from core.models import User
from django.db.models import Avg

# Create your models here.

class TrackRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    track_id = models.CharField(max_length=100)
    track_name = models.CharField(max_length=255)
    artist_name = models.CharField(max_length=255)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'track_id']
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} rated {self.track_name} - {self.artist_name} as {self.rating}/5"
    
    @classmethod
    def get_average_rating(cls, track_id):
        """Get the average rating for a track across all users"""
        result = cls.objects.filter(track_id=track_id).aggregate(
            avg_rating=Avg('rating'),
            rating_count=models.Count('rating')
        )
        return {
            'average': round(result['avg_rating'], 1) if result['avg_rating'] else None,
            'count': result['rating_count']
        }
