from django.db import models
from django.utils import timezone
from component.user.models import Child  # Import Parent model
import uuid

class EducationalMaterial(models.Model):
    MATERIAL_TYPE_CHOICES = [
        ('book', 'Book'),
        ('video', 'Video'),
    ]

    eduMaterialID = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.BooleanField(default=True)  # Game status (active or inactive)
    type = models.CharField(max_length=10, choices=MATERIAL_TYPE_CHOICES)  # Book or Video
    file_url = models.URLField(blank=True, null=True)  # URL of the uploaded file (PDF for books or video URL)
    thumbnail_url = models.URLField(blank=True, null=True)  # URL of the thumbnail image for books

    def __str__(self):
        return self.title

class ChildEduMaterial(models.Model):
    childEduMaterialID = models.CharField(max_length=100, primary_key=True)
    accessDate = models.DateTimeField(default=timezone.now)
    timeSpent = models.IntegerField(default=0)  # Time spent in seconds
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='child_edu_materials')
    eduMaterial = models.ForeignKey(EducationalMaterial, on_delete=models.CASCADE, related_name='child_edu_materials')

    def __str__(self):
        return f"{self.child.name} - {self.eduMaterial.title}"

    def record_time_spent(self, time_spent):
        """Record time spent on the educational material"""
        self.timeSpent += time_spent
        self.save()

    def record_access_date(self):
        """Update access date to the current date"""
        self.accessDate = timezone.now()
        self.save()