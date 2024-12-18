from django.db import models
from django.utils import timezone
import uuid
from component.user.models import Parent  # Assuming you have a Parent model

# Child model needs to be imported from its corresponding module
from component.user.models import Child


class GameType(models.Model):
    typeID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    type_name = models.CharField(max_length=100)  # E.g., "Match the Word", "Correct the Spelling"

    def __str__(self):
        return self.type_name  # Use type_name for display


class GameQuestion(models.Model):
    gameQuestionID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    question = models.TextField()  # Question text
    # Remove the 'answer' field if it is not defined or necessary here.
    # answer = models.CharField(max_length=200)  # Remove or correct this line

    def get_game_question_id(self):
        return self.gameQuestionID

    def __str__(self):
        return self.question  # Display question text

class GameQuestionOption(models.Model):
    optionID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    question = models.ForeignKey(GameQuestion, related_name='options', on_delete=models.CASCADE)
    image_url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=200, null=True, blank=True)  # Text for the option, if any
    is_correct = models.BooleanField(default=False)  # Indicates if this option is the correct answer

    def __str__(self):
        return f"Option: {self.text or self.image_url} (Correct: {self.is_correct})"


class Game(models.Model):
    gameID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    title = models.CharField(max_length=100, null=True, blank=True)  # Game title
    thumbnail_url = models.URLField(null=True, blank=True)  # URL to store game logo
    description = models.TextField(null=True, blank=True)  # Description of the game
    free = models.BooleanField(default=True)  # Indicate if the game is free or not
    status = models.BooleanField(default=True)  # Game status (active or inactive)
    template_name = models.CharField(max_length=200, null=True, blank=True)

    questions = models.ManyToManyField(GameQuestion, related_name='quizzes')
    type = models.ForeignKey(GameType, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='games')  # Reference to GameType

    def get_game_id(self):
        return self.gameID

    def __str__(self):
        return self.title  # Display title as string representation


class ChildGame(models.Model):
    childGameID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    playDate = models.DateTimeField(default=timezone.now)  # Automatically set the play date
    timeSpent = models.DurationField(null=True, blank=True)  # Duration field to store time spent on the game
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='child_games')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='child_games')

    def get_child_game_id(self):
        return self.childGameID

    def __str__(self):
        return f"{self.child.name} - {self.game.title}"  # Display child name and game title


class ChildGameLog(models.Model):
    childGameLogID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    access_date = models.DateTimeField(default=timezone.now)  # Automatically set the play date
    time_spent = models.DurationField()  # Duration field to store time spent on the game
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='child_games_log')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='child_games_log')

