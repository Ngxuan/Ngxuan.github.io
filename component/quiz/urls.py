# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('quiz/<uuid:childID>/<uuid:quizID>/', views.quiz_page, name='quiz_page'),
    path('save_result/', views.save_quiz_result, name='save_quiz_result'),
]
