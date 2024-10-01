# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('quiz/<uuid:childID>/<uuid:quizID>/', views.quiz_page, name='quiz_page'),
    path('quizzes/save_result/<uuid:child_quiz_id>/', views.save_quiz_result, name='save_quiz_result'),
]
