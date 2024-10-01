# component/eduMaterial/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Update URL pattern to use eduMaterialID instead of bookID
    path('book/<uuid:childID>/<uuid:eduMaterialID>/', views.book_viewer, name='book_viewer'),
]
