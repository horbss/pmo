from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from social.models import Post, Follow
from spotify.models import TrackRating
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create dummy data for testing the social features'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of users to create (default: 10)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new data'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            # Keep the current user (first superuser) but clear others
            User.objects.filter(is_superuser=False).delete()
            Post.objects.all().delete()
            Follow.objects.all().delete()
            TrackRating.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        num_users = options['users']
        self.stdout.write(f'Creating {num_users} dummy users...')

        # Sample user data
        user_data = [
            {'username': 'music_lover_42', 'email': 'musiclover@example.com', 'first_name': 'Alex', 'last_name': 'Johnson'},
            {'username': 'indie_vibes', 'email': 'indievibes@example.com', 'first_name': 'Emma', 'last_name': 'Smith'},
            {'username': 'rock_star_99', 'email': 'rockstar@example.com', 'first_name': 'Jake', 'last_name': 'Wilson'},
            {'username': 'jazz_enthusiast', 'email': 'jazz@example.com', 'first_name': 'Sophia', 'last_name': 'Brown'},
            {'username': 'pop_princess', 'email': 'popprincess@example.com', 'first_name': 'Olivia', 'last_name': 'Davis'},
            {'username': 'hip_hop_head', 'email': 'hiphop@example.com', 'first_name': 'Marcus', 'last_name': 'Garcia'},
            {'username': 'electronic_beats', 'email': 'electronic@example.com', 'first_name': 'Luna', 'last_name': 'Martinez'},
            {'username': 'classical_soul', 'email': 'classical@example.com', 'first_name': 'David', 'last_name': 'Anderson'},
            {'username': 'reggae_rhythm', 'email': 'reggae@example.com', 'first_name': 'Maya', 'last_name': 'Thompson'},
            {'username': 'country_roads', 'email': 'country@example.com', 'first_name': 'Tyler', 'last_name': 'White'},
            {'username': 'metalhead_666', 'email': 'metal@example.com', 'first_name': 'Zoe', 'last_name': 'Taylor'},
            {'username': 'funk_master', 'email': 'funk@example.com', 'first_name': 'Carlos', 'last_name': 'Rodriguez'},
        ]

        # Sample Spotify albums data
        sample_albums = [
            {
                'id': '4yP0hdKOZPNshxUOjY0cZj',
                'name': 'Abbey Road',
                'image': 'https://i.scdn.co/image/ab67616d0000b273dc30583ba717007b00cceb25'
            },
            {
                'id': '2guirTSEqLizK7j9i1MTTZ',
                'name': 'The Dark Side of the Moon',
                'image': 'https://i.scdn.co/image/ab67616d0000b273ea7caaff71dea1051d49b2fe'
            },
            {
                'id': '6dVIqQ8qmQ5GBnJ9shOYGE',
                'name': 'Random Access Memories',
                'image': 'https://i.scdn.co/image/ab67616d0000b27351afaa45b68f94f98c4c73c4'
            },
            {
                'id': '4q3ewBCX7sLwd24euuV69X',
                'name': 'Bad',
                'image': 'https://i.scdn.co/image/ab67616d0000b2732b7dc6d96055b229ab22c0c0'
            },
            {
                'id': '1DFixLWuPkv3KT3TnV35m3',
                'name': 'Blond',
                'image': 'https://i.scdn.co/image/ab67616d0000b273c5649add07ed3720be9d5526'
            }
        ]

        # Sample Spotify artists data
        sample_artists = [
            {
                'id': '3TVXtAsR1Inumwj472S9r4',
                'name': 'Drake',
                'image': 'https://i.scdn.co/image/ab6761610000e5ebb19af0ea736c6228d6eb539c'
            },
            {
                'id': '06HL4z0CvFAxyc27GXpf02',
                'name': 'Taylor Swift',
                'image': 'https://i.scdn.co/image/ab6761610000e5ebe672b5f553298dcdccb0e676'
            },
            {
                'id': '4q3ewBCX7sLwd24euuV69X',
                'name': 'Michael Jackson',
                'image': 'https://i.scdn.co/image/ab6761610000e5ebceb7e2fc34f853bb2b99ec3d'
            },
            {
                'id': '0L8ExT028jH3ddEcZwqJJ5',
                'name': 'Red Hot Chili Peppers',
                'image': 'https://i.scdn.co/image/ab6761610000e5eb4f7fea01ae4e1d936090a2ad'
            },
            {
                'id': '1dfeR4HaWDbWqFHLkxsg1d',
                'name': 'Queen',
                'image': 'https://i.scdn.co/image/ab6761610000e5ebb19af0ea736c6228d6eb539c'
            }
        ]

        # Sample tracks for posts
        sample_tracks = [
            {
                'id': '0VjIjW4GlULA5U9j1qbnM8',
                'name': 'Blinding Lights',
                'artist': 'The Weeknd',
                'image': 'https://i.scdn.co/image/ab67616d0000b2734f39af0b65dc4f4e5daccf13',
                'url': 'https://open.spotify.com/track/0VjIjW4GlULA5U9j1qbnM8'
            },
            {
                'id': '11dFghVXANMlKmJXsNCbNl',
                'name': 'good 4 u',
                'artist': 'Olivia Rodrigo',
                'image': 'https://i.scdn.co/image/ab67616d0000b273a91c10fe9472d9bd89802e5a',
                'url': 'https://open.spotify.com/track/11dFghVXANMlKmJXsNCbNl'
            },
            {
                'id': '1Ax1SxYJ8lM5ZZ7gU39QVa',
                'name': 'Heat Waves',
                'artist': 'Glass Animals',
                'image': 'https://i.scdn.co/image/ab67616d0000b273a07e7fa5af2b076b5c43bc00',
                'url': 'https://open.spotify.com/track/1Ax1SxYJ8lM5ZZ7gU39QVa'
            },
            {
                'id': '4iV5W9uYEdYUVa79Axb7Rh',
                'name': 'As It Was',
                'artist': 'Harry Styles',
                'image': 'https://i.scdn.co/image/ab67616d0000b273b46f74097655d7f353caab14',
                'url': 'https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh'
            },
            {
                'id': '60nZcImufyMA1MKQY3dcCH',
                'name': 'Anti-Hero',
                'artist': 'Taylor Swift',
                'image': 'https://i.scdn.co/image/ab67616d0000b273bb54dde68cd23e2a268ae0f5',
                'url': 'https://open.spotify.com/track/60nZcImufyMA1MKQY3dcCH'
            }
        ]

        # Sample album posts data
        sample_album_posts = [
            {
                'id': '4yP0hdKOZPNshxUOjY0cZj',
                'name': 'Abbey Road',
                'artist': 'The Beatles',
                'image': 'https://i.scdn.co/image/ab67616d0000b273dc30583ba717007b00cceb25',
                'url': 'https://open.spotify.com/album/4yP0hdKOZPNshxUOjY0cZj'
            },
            {
                'id': '2guirTSEqLizK7j9i1MTTZ',
                'name': 'The Dark Side of the Moon',
                'artist': 'Pink Floyd',
                'image': 'https://i.scdn.co/image/ab67616d0000b273ea7caaff71dea1051d49b2fe',
                'url': 'https://open.spotify.com/album/2guirTSEqLizK7j9i1MTTZ'
            }
        ]

        # Sample post content
        sample_comments = [
            "This track is absolutely incredible! 🎵",
            "Can't stop listening to this one",
            "Perfect for a rainy day ☔",
            "This brings back so many memories",
            "Found my new favorite song!",
            "The production on this is insane",
            "This artist never disappoints",
            "On repeat all day long",
            "Such a vibe! Love it",
            "This hits different at 3am",
            "Pure musical genius",
            "This album changed my life",
            "Incredible vocals and lyrics",
            "This deserves all the awards",
            "Finally, some good music!"
        ]

        created_users = []
        
        # Create users
        for i in range(min(num_users, len(user_data))):
            data = user_data[i]
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'spotify_access_token': 'dummy_token_' + str(i),
                    'spotify_id': f'spotify_user_{i}',
                    'listen_later': f'playlist_{i}'
                }
            )
            
            if created:
                # Add some top albums and artists
                if i < len(sample_albums):
                    album = sample_albums[i % len(sample_albums)]
                    user.top_album1_id = album['id']
                    user.top_album1_name = album['name']
                    user.top_album1_image = album['image']
                
                if (i + 1) < len(sample_albums):
                    album = sample_albums[(i + 1) % len(sample_albums)]
                    user.top_album2_id = album['id']
                    user.top_album2_name = album['name']
                    user.top_album2_image = album['image']
                
                if i < len(sample_artists):
                    artist = sample_artists[i % len(sample_artists)]
                    user.top_artist1_id = artist['id']
                    user.top_artist1_name = artist['name']
                    user.top_artist1_image = artist['image']
                
                user.save()
                self.stdout.write(f'Created user: {user.username}')
            
            created_users.append(user)

        # Create some posts
        self.stdout.write('\nCreating posts...')
        for user in created_users:
            # Create 2-4 posts per user
            num_posts = random.randint(2, 4)
            for _ in range(num_posts):
                if random.choice([True, False]):  # Track post
                    track = random.choice(sample_tracks)
                    Post.objects.create(
                        user=user,
                        post_type='track',
                        content=random.choice(sample_comments),
                        spotify_id=track['id'],
                        spotify_name=track['name'],
                        spotify_artist=track['artist'],
                        spotify_image_url=track['image'],
                        spotify_url=track['url'],
                        rating=random.choice([None, None, round(random.uniform(6.0, 10.0), 1)])
                    )
                else:  # Album post
                    album = random.choice(sample_album_posts)
                    Post.objects.create(
                        user=user,
                        post_type='album',
                        content=random.choice(sample_comments),
                        spotify_id=album['id'],
                        spotify_name=album['name'],
                        spotify_artist=album['artist'],
                        spotify_image_url=album['image'],
                        spotify_url=album['url'],
                        rating=round(random.uniform(7.0, 10.0), 1)
                    )

        # Create some track ratings
        self.stdout.write('Creating track ratings...')
        for user in created_users:
            # Each user rates 3-5 random tracks
            num_ratings = random.randint(3, 5)
            rated_tracks = random.sample(sample_tracks, min(num_ratings, len(sample_tracks)))
            
            for track in rated_tracks:
                TrackRating.objects.get_or_create(
                    user=user,
                    track_id=track['id'],
                    defaults={
                        'track_name': track['name'],
                        'artist_name': track['artist'],
                        'rating': round(random.uniform(6.0, 10.0), 1)
                    }
                )

        # Create follow relationships
        self.stdout.write('Creating follow relationships...')
        for user in created_users:
            # Each user follows 3-6 other users
            possible_follows = [u for u in created_users if u != user]
            num_follows = random.randint(3, min(6, len(possible_follows)))
            users_to_follow = random.sample(possible_follows, num_follows)
            
            for follow_user in users_to_follow:
                Follow.objects.get_or_create(
                    follower=user,
                    following=follow_user
                )

        # Print summary
        total_users = User.objects.count()
        total_posts = Post.objects.count()
        total_follows = Follow.objects.count()
        total_ratings = TrackRating.objects.count()

        self.stdout.write(self.style.SUCCESS('\n✅ Dummy data created successfully!'))
        self.stdout.write(f'📊 Summary:')
        self.stdout.write(f'  👥 Total users: {total_users}')
        self.stdout.write(f'  📝 Total posts: {total_posts}')
        self.stdout.write(f'  🤝 Total follows: {total_follows}')
        self.stdout.write(f'  ⭐ Total ratings: {total_ratings}')
        self.stdout.write('\n🎉 You can now test the social features!')
        self.stdout.write('💡 Try visiting /social/discover/ to find users to follow')
        self.stdout.write('💡 Check your /social/feed/ to see posts from followed users') 