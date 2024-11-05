
from django.utils import timezone
from component.user.models import Child

from django.db import models
import uuid
from component.quiz.models import QuizType

class Achievement(models.Model):
    ACHIEVEMENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('book', 'Book'),
        ('game', 'Game'),
        ('quiz', 'Quiz'),
    ]

    COMPLETION_METRIC_CHOICES = [
        ('time_spent', 'Time Spent'),
        ('score', 'Score'),
        ('explore', 'Explore'),
    ]

    achievementID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    thumbnail_url = models.URLField(null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    type = models.CharField(max_length=50, choices=ACHIEVEMENT_TYPE_CHOICES, default='video')
    completion_metric = models.CharField(max_length=50, choices=COMPLETION_METRIC_CHOICES, default='time_spent')
    criteria = models.FloatField()
    status = models.BooleanField(default=True)

    quiz_type = models.ForeignKey(QuizType, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='achievements')

    def __str__(self):
        return self.title




class ChildAchievement(models.Model):
    """
    ChildAchievement model represents the achievements of a child.
    """
    childAchievementID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    dateEarned = models.DateTimeField(default=timezone.now)  # Date the achievement was earned
    completionPercentage = models.FloatField(default=0.0)  # Percentage of completion for the achievement
    complete = models.BooleanField(default=False)  # Whether the achievement is completed or not
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='child_achievements')
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='child_achievements', to_field='childID')

    def get_child_achievement_id(self):
        return str(self.childAchievementID)



    def calculate_completion_percentage(self, completion_percentage):
        """
        Updates the completion percentage and marks the achievement as complete if it reaches 100.
        """
        self.completionPercentage = min(completion_percentage, 100)  # Ensure it doesn't exceed 100

        # Mark as complete if the completion percentage is 100
        if self.completionPercentage >= 100:
            self.complete = True
            self.dateEarned = timezone.now()
        else:
            self.complete = False  # Optionally reset to False if not complete

        self.save()  # Save the updated achievement percentage
        print("Child Achievement saved with completion percentage:", self.completionPercentage)

    def __str__(self):
        return f"{self.child.name} - {self.achievement.title} (Completed: {self.complete})"
