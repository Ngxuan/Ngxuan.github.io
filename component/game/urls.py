# urls.py
from django.urls import path
from . import views


urlpatterns = [
    # The URL pattern should match the order of parameters in the view function
    path('play/<uuid:child_id>/<uuid:game_id>/', views.play_game, name='play_game'),
]