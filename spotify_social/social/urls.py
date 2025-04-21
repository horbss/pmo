from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('create-post/', views.create_post, name='create_post'),
    path('add-to-queue/', views.add_to_queue, name='add_to_queue'),
] 