print("signals.py is loaded")  # Debugging print to confirm file import

from django.db.models.signals import post_save
from django.dispatch import receiver
from component.user.models import Child
from .models import Achievement, ChildAchievement
from component.eduMaterial.models import ChildEduMaterial
from component.game.models import ChildGame
from component.quiz.models import ChildQuiz


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
    'ChildEduMaterial': 'video',  # Example mapping
    'ChildGame': 'game',           # Example mapping
    'ChildQuiz': 'quiz'            # Ensure 'quiz' matches the choice in ACHIEVEMENT_TYPE_CHOICES
}


@receiver(post_save, sender=ChildEduMaterial)
@receiver(post_save, sender=ChildGame)
@receiver(post_save, sender=ChildQuiz)
def update_child_achievement(sender, instance, **kwargs):
    try:
        child = instance.child
        print(f"Updating achievement for child: {child.childID}, content type: {sender.__name__}")

        content_type = sender.__name__  # Get the content type
        achievement_type = CONTENT_TYPE_TO_ACHIEVEMENT_TYPE.get(content_type)

        if achievement_type is None:
            print(f"No mapping found for content type: {content_type}")
            return  # Exit if no mapping found

        print(f"Content type for achievements: {achievement_type}")

        # Initialize achievements queryset
        achievements = Achievement.objects.all()

        # If the content type is ChildQuiz, filter achievements by quiz type
        if content_type == 'ChildQuiz':
            quiz_type_id = instance.quiz.type.typeID  # Assuming quiz has a ForeignKey to QuizType
            print(f"Filtering achievements by Quiz Type ID: {quiz_type_id}")
            achievements = achievements.filter(quiz_type=quiz_type_id)  # Filter achievements by quiz type

        # Retrieve achievements based on mapped type
        achievements = achievements.filter(type=achievement_type)
        print(f"Retrieved achievements: {[ach.achievementID for ach in achievements]}")  # Use achievementID

        for achievement in achievements:
            try:
                print(f"Processing achievement: {achievement.achievementID} for child: {child.childID}")
                child_achievement, created = ChildAchievement.objects.get_or_create(child=child, achievement=achievement)

                # Check if achievement is already completed
                if child_achievement.complete:
                    print(f"Achievement {achievement.achievementID} is already completed. Skipping update.")
                    continue  # Skip to the next achievement if it's already completed

                progress_value = 0
                completion_percentage = 0

                if achievement.completion_metric == 'time_spent':
                    progress_value = (instance.timeSpent.total_seconds() / 3600) if instance.timeSpent else 0
                    completion_percentage = float(progress_value / achievement.criteria) * 100
                    print(f"Time spent: {progress_value}, Completion Percentage: {completion_percentage}")

                elif achievement.completion_metric == 'score':
                    progress_value = instance.score if hasattr(instance, 'score') else 0
                    completion_percentage = float(progress_value / achievement.criteria) * 100
                    print(f"Score: {progress_value}, Completion Percentage: {completion_percentage}")

                elif achievement.completion_metric == 'explore':
                    if content_type == 'ChildEduMaterial':
                        unique_items = ChildEduMaterial.objects.filter(child=child).values('edu_material').distinct().count()
                    elif content_type == 'ChildGame':
                        unique_items = ChildGame.objects.filter(child=child).values('game').distinct().count()
                    elif content_type == 'ChildQuiz':
                        unique_items = ChildQuiz.objects.filter(child=child).values('quiz').distinct().count()

                    progress_value = unique_items
                    completion_percentage = float(progress_value / achievement.criteria) * 100
                    print(f"Unique items accessed: {unique_items}, Completion Percentage: {completion_percentage}")

                # Update the child's achievement completion
                child_achievement.calculate_completion_percentage(completion_percentage)
                print(f"Child Achievement Updated: {child_achievement.childAchievementID}, Completion Percentage: {completion_percentage}")

            except Exception as e:
                print(f"Error processing achievement {achievement.achievementID}: {e}")

    except Exception as e:
        print(f"Error in update_child_achievement: {e}")
