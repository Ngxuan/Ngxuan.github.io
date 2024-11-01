from django.db import models
import uuid
from django.utils import timezone


class Achievement(models.Model):
    """
    Achievement model stores the details of each achievement.
    """
    achievementID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    thumbnail_url = models.URLField(null=True, blank=True)  # URL to store game logo
    title = models.CharField(max_length=255)  # Achievement title
    description = models.TextField()  # Description of the achievement
    criteria = models.TextField()  # Criteria for completing the achievement
    rewards = models.TextField()  # Rewards associated with the achievement
    status = models.BooleanField(default=True)  # Whether the achievement is active or not

    def get_achievement_id(self):
        return str(self.achievementID)

    def __str__(self):
        return self.title  # Display the achievement title


class Child(models.Model):
    """
    A placeholder Child model, assuming this model is already defined elsewhere.
    """
    childID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    name = models.CharField(max_length=100)
    # Add other relevant fields here


class ChildAchievement(models.Model):
    """
    ChildAchievement model represents the achievements of a child.
    """
    childAchievementID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    dateEarned = models.DateTimeField(default=timezone.now)  # Date the achievement was earned
    completionPercentage = models.FloatField(default=0.0)  # Percentage of completion for the achievement
    complete = models.BooleanField(default=False)  # Whether the achievement is completed or not
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='child_achievements')
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='child_achievements')

    def get_child_achievement_id(self):
        return str(self.childAchievementID)

    def mark_as_completed(self):
        """
        Marks the achievement as completed and sets the completion percentage to 100.
        """
        self.complete = True
        self.completionPercentage = 100.0
        self.save()

    def calculate_completion_percentage(self, value):
        """
        Calculates and updates the completion percentage based on a given value.
        """
        self.completionPercentage = value
        self.save()

    def __str__(self):
        return f"{self.child.name} - {self.achievement.title} (Completed: {self.complete})"
