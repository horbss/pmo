from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('create-post/', views.create_post, name='create_post'),
    path('edit-post/<int:post_id>/', views.edit_post, name='edit_post'),
    path('add-to-queue/', views.add_to_queue, name='add_to_queue'),
    path('add-to-listen-later/', views.add_to_listen_later, name='add_to_listen_later'),
    path('delete-post/<int:post_id>/', views.delete_post, name='delete_post'),
    
    # Like and Comment URLs
    path('like-post/<int:post_id>/', views.like_post, name='like_post'),
    path('add-comment/<int:post_id>/', views.add_comment, name='add_comment'),
    path('get-comments/<int:post_id>/', views.get_comments, name='get_comments'),
    
    # Follow system URLs
    path('discover/', views.discover_users, name='discover_users'),
    path('feed/', views.feed, name='feed'),
    path('follow/<int:user_id>/', views.follow_user, name='follow_user'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow_user'),
    path('following/', views.following_list, name='following_list'),
    path('following/<int:user_id>/', views.following_list, name='user_following_list'),
    path('followers/', views.followers_list, name='followers_list'),
    path('followers/<int:user_id>/', views.followers_list, name='user_followers_list'),
    path('user/<int:user_id>/', views.user_profile, name='user_profile'),
] 