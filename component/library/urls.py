# library/urls.py

from django.urls import path
from . import views
from .views import pdf_to_tts_view

urlpatterns = [
    path('library/', views.library, name='library'),  # This URL points to the library view
    path('pdf-to-tts/', pdf_to_tts_view, name='pdf_to_tts_view'),

]
