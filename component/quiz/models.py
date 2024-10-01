from django.db import models
from django.utils import timezone
from component.user.models import Child  # Import Child model
import uuid

class QuizQuestion(models.Model):
    quizQuestionID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    question = models.TextField()
    # Removing old fields for options and answers
    # option = models.JSONField()
    # answer = models.JSONField()

    def get_quiz_question_id(self):
        return self.quizQuestionID

    def __str__(self):
        return self.question


class QuizQuestionOption(models.Model):
    optionID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    question = models.ForeignKey(QuizQuestion, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=200)  # Option text
    is_correct = models.BooleanField(default=False)  # Indicates if this option is the correct answer

    def __str__(self):
        return f"Option: {self.text} (Correct: {self.is_correct})"


class Quiz(models.Model):
    quizID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    title = models.CharField(max_length=100, null=True, blank=True)


    thumbnail_url  = models.URLField(blank=True, null=True)
    status = models.BooleanField(default=False)
    questions = models.ManyToManyField(QuizQuestion, related_name='quizzes')

    def get_quiz_id(self):
        return self.quizID

    def __str__(self):
        return self.title  # Use the title for display



class ChildQuiz(models.Model):
    childQuizID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    startDate = models.DateTimeField(default=timezone.now)  # Automatically set the start time
    status = models.BooleanField(default=False)
    score = models.FloatField(default=0.0)  # Float field to handle decimals and large scores
    correct_answers = models.PositiveIntegerField(default=0)  # Use PositiveIntegerField for correct answers
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='child_quizzes')
    quiz = models.ForeignKey('Quiz', on_delete=models.CASCADE, related_name='child_quizzes')
    timeSpent = models.DurationField(null=True, blank=True)  # Duration field to store time spent

    def get_child_quiz_id(self):
        return self.childQuizID

    def __str__(self):
        return f"{self.child.name} - {self.quiz.title}"  # Use quiz title for display
