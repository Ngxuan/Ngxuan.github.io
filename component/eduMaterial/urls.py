# component/eduMaterial/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Update URL pattern to use eduMaterialID instead of bookID
    path('book/<uuid:childID>/<uuid:eduMaterialID>/', views.book_viewer, name='book_viewer'),
    path('record_time_spent/<uuid:childID>/<uuid:eduMaterialID>/', views.record_time_spent, name='record_time_spent'),
]
