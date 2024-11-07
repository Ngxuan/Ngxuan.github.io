import datetime

print("signals.py is loaded")  # Debugging print to confirm file import

from component.user.models import Child
from .models import Achievement, ChildAchievement
from component.eduMaterial.models import ChildEduMaterial
from component.game.models import ChildGame
from component.quiz.models import ChildQuiz
from django.db.models import Sum
from django.dispatch import receiver
from django.db.models.signals import post_save


@receiver(post_save, sender=Achievement)
def assign_achievement_to_all_children(sender, instance, created, **kwargs):
    if created:
        print("Signal received: New achievement created")  # Debugging print
        children = Child.objects.all()
        for child in children:
            ChildAchievement.objects.create(
                achievement=instance,
                child=child
            )

@receiver(post_save, sender=Child)
def assign_all_achievements_to_child(sender, instance, created, **kwargs):
    if created:
        print("Signal received: New child created")  # Debugging print
        achievements = Achievement.objects.all()
        for achievement in achievements:
            ChildAchievement.objects.create(
                achievement=achievement,
                child=instance
            )


# Map content types to achievement types
CONTENT_TYPE_TO_ACHIEVEMENT_TYPE = {
    'ChildEduMaterial': {
        'book': 'book',    # Map books to 'book'
        'video': 'video'   # Map videos to 'video'
    },
    'ChildGame': 'game',           # Example mapping
    'ChildQuiz': 'quiz'            # Ensure 'quiz' matches the choice in ACHIEVEMENT_TYPE_CHOICES
}

import datetime
from django.db.models import Sum


@receiver(post_save, sender=ChildEduMaterial)
@receiver(post_save, sender=ChildGame)
@receiver(post_save, sender=ChildQuiz)
def update_child_achievement(sender, instance, **kwargs):
    try:
        child = instance.child
        print(f"Updating achievement for child: {child.childID}, content type: {sender.__name__}")

        content_type = sender.__name__

        # Determine the achievement type based on content type and material type
        if content_type == 'ChildEduMaterial':
            material_type = instance.eduMaterial.type  # Access type from the related EducationalMaterial instance
            achievement_type = CONTENT_TYPE_TO_ACHIEVEMENT_TYPE.get(content_type, {}).get(material_type)
        else:
            achievement_type = CONTENT_TYPE_TO_ACHIEVEMENT_TYPE.get(content_type)

        if achievement_type is None:
            print(f"No mapping found for content type: {content_type} with material type: {material_type}")
            return  # Exit if no mapping found

        print(f"Achievement type for this content: {achievement_type}")

        # Fetch achievements matching the determined type
        achievements = Achievement.objects.filter(type=achievement_type)

        for achievement in achievements:
            try:
                print(f"Processing achievement: {achievement.achievementID} for child: {child.childID}")
                child_achievement, created = ChildAchievement.objects.get_or_create(child=child, achievement=achievement)

                # Check if the achievement is already completed
                if child_achievement.complete:
                    print(f"Achievement {achievement.achievementID} is already completed. Skipping update.")
                    continue

                # Initialize progress_value
                progress_value = 0

                # Calculate progress based on completion metric
                if achievement.completion_metric == 'time_spent':
                    total_time_spent = ChildQuiz.objects.filter(child=child, quiz=achievement.quiz_title).aggregate(
                        total_time=Sum('timeSpent')
                    )['total_time'] or 0

                    if isinstance(total_time_spent, datetime.timedelta):
                        total_time_spent = total_time_spent.total_seconds()

                    progress_value = total_time_spent  # In seconds
                    print(f"Time spent (seconds): {progress_value}")

                elif achievement.completion_metric == 'score':
                    total_score = ChildQuiz.objects.filter(child=child, quiz=achievement.quiz_title).aggregate(
                        total_score=Sum('score')
                    )['total_score'] or 0
                    progress_value = total_score
                    print(f"Total score: {progress_value}")

                elif achievement.completion_metric == 'explore':
                    if content_type == 'ChildEduMaterial':
                        unique_books = ChildEduMaterial.objects.filter(
                            child=child, eduMaterial__type='book'  # Access type through related EducationalMaterial
                        ).values('eduMaterial').distinct().count()

                        unique_videos = ChildEduMaterial.objects.filter(
                            child=child, eduMaterial__type='video'
                        ).values('eduMaterial').distinct().count()

                        progress_value = unique_books + unique_videos  # Adjust based on your needs
                        print(f"Unique books accessed: {unique_books}")
                        print(f"Unique videos accessed: {unique_videos}")

                    elif content_type == 'ChildGame':
                        unique_items = ChildGame.objects.filter(child=child).values('game').distinct().count()
                        progress_value = unique_items
                        print(f"Unique games accessed: {unique_items}")

                    elif content_type == 'ChildQuiz':
                        unique_items = ChildQuiz.objects.filter(child=child).values('quiz').distinct().count()
                        progress_value = unique_items
                        print(f"Unique quizzes accessed: {unique_items}")

                # Calculate completion percentage
                completion_percentage = (progress_value / achievement.criteria) * 100 if achievement.criteria > 0 else 0
                print(f"Completion Percentage: {completion_percentage}")

                # Update child achievement progress
                child_achievement.progress_value = progress_value
                child_achievement.complete = completion_percentage >= 100
                child_achievement.save()

                print(
                    f"Child Achievement Updated: {child_achievement.childAchievementID}, Completion Percentage: {completion_percentage}")

            except Exception as e:
                print(f"Error processing achievement {achievement.achievementID}: {e}")

    except Exception as e:
        print(f"Error in update_child_achievement: {e}")