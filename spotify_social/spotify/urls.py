from django.urls import path
from . import views

app_name = 'spotify'

urlpatterns = [
    path('login/', views.spotify_login, name='spotify_login'),
    path('callback/', views.spotify_callback, name='spotify_callback'),
    path('disconnect/', views.spotify_disconnect, name='spotify_disconnect'),
    path('search/', views.spotify_search, name='spotify_search'),
    path('search-page/', views.search_page, name='search_page'),
    path('rate-track/', views.rate_track, name='rate_track'),
    path('get-token/', views.get_spotify_token, name='get_spotify_token'),
    path('get-top-albums/', views.get_top_albums, name='get_top_albums'),
    path('remove-from-playlist/', views.remove_from_playlist, name='remove_from_playlist'),
] 