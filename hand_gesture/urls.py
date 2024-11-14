# hand_gesture/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('video_feed/', views.video_feed, name='video_feed'),
    path('get_last_gesture/', views.get_last_gesture, name='get_last_gesture'),
]
