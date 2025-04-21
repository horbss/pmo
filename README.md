# Spotify Social

A social media platform for music lovers where every post must include a Spotify track. Share your favorite songs, discover new music, and connect with other music enthusiasts.

> **Note**: This is a class project and not open source.

## 🎵 Features

- **Music-Centric Posts**: Every post must include a Spotify track
- **Social Features**:
  - Like and comment on posts
  - Follow other users
  - View your personalized music feed
- **Spotify Integration**:
  - Search and attach Spotify tracks to posts
  - View track details and previews
  - Share your music taste with others

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- Django
- Spotify Developer Account (for API access)
- PostgreSQL (recommended)

### Installation

1. Clone the repository:
   ```bash
   git clone [your-repo-url]
   cd spotify_social
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file with:
   ```
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   SECRET_KEY=your_django_secret_key
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## 📱 Usage

1. Sign up for an account
2. Connect your Spotify account
3. Start sharing your favorite tracks with the community
4. Follow other users and discover new music
5. Like and comment on posts

## 🛠️ Tech Stack

- **Backend**: Django
- **Frontend**: HTML, CSS, JavaScript
- **Database**: PostgreSQL
- **Authentication**: Django Authentication
- **API Integration**: Spotify Web API

## 🙏 Acknowledgments

- Spotify for their amazing API
- Django community for the fantastic framework
