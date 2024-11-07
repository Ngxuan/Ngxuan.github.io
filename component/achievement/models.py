
from django.utils import timezone
from component.user.models import Child

from django.db import models
import uuid
from component.quiz.models import Quiz

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

    quiz_title = models.ForeignKey(Quiz, on_delete=models.SET_NULL, null=True, blank=True, related_name='achievements')

    def __str__(self):
        return self.title




class ChildAchievement(models.Model):
    """
    ChildAchievement model represents the achievements of a child.
    """
    childAchievementID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    dateEarned = models.DateTimeField(default=timezone.now)  # Date the achievement was earned
    progress_value = models.FloatField(default=0.0)
    complete = models.BooleanField(default=False)  # Whether the achievement is completed or not
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='child_achievements')
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='child_achievements', to_field='childID')

    def get_child_achievement_id(self):
        return str(self.childAchievementID)

    def calculate_completion(self):
        """
        Calculates the completion percentage based on progress_value and marks the achievement as complete if it reaches 100%.
        """
        # Calculate completion percentage dynamically
        if self.achievement.criteria > 0:
            completion_percentage = (self.progress_value / self.achievement.criteria) * 100
        else:
            completion_percentage = 0

        # Ensure the completion percentage does not exceed 100
        completion_percentage = min(completion_percentage, 100)

        # Update the `complete` status based on the completion percentage
        if completion_percentage >= 100:
            self.complete = True
            self.dateEarned = timezone.now()  # Set the date when marked complete
        else:
            self.complete = False

        self.save()  # Save the updated achievement
        print("Child Achievement saved with calculated completion percentage:", completion_percentage)

    def __str__(self):
        return f"{self.child.name} - {self.achievement.title} (Completed: {self.complete})"