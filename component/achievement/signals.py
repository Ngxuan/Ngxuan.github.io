# signals.py

import logging
from datetime import datetime

from django.db.models import Sum
from django.dispatch import receiver
from django.db.models.signals import post_save
from component.user.models import Child
from .models import Achievement, ChildAchievement
from component.eduMaterial.models import ChildEduMaterial
from component.game.models import ChildGame
from component.quiz.models import ChildQuiz

# Configure logging
logger = logging.getLogger(__name__)

# Map content types to achievement types
CONTENT_TYPE_TO_ACHIEVEMENT_TYPE = {
    'ChildEduMaterial': {
        'book': 'book',    # Map books to 'book'
        'video': 'video'   # Map videos to 'video'
    },
    'ChildGame': 'game',       # Example mapping
    'ChildQuiz': 'quiz'        # Ensure 'quiz' matches the choice in ACHIEVEMENT_TYPE_CHOICES
}

@receiver(post_save, sender=Achievement)
def assign_achievement_to_all_children(sender, instance, created, **kwargs):
    if created:
        logger.debug("Signal received: New achievement created")
        children = Child.objects.all()
        ChildAchievement.objects.bulk_create([
            ChildAchievement(achievement=instance, child=child)
            for child in children
        ])
        logger.debug(f"Assigned achievement '{instance.title}' to all children.")

@receiver(post_save, sender=Child)
def assign_all_achievements_to_child(sender, instance, created, **kwargs):
    if created:
        logger.debug("Signal received: New child created")
        achievements = Achievement.objects.all()
        ChildAchievement.objects.bulk_create([
            ChildAchievement(achievement=achievement, child=instance)
            for achievement in achievements
        ])
        logger.debug(f"Assigned all achievements to child '{instance.childID}'.")

@receiver(post_save, sender=ChildEduMaterial)
@receiver(post_save, sender=ChildGame)
@receiver(post_save, sender=ChildQuiz)
def update_child_achievement(sender, instance, **kwargs):
    try:
        child = instance.child
        content_type = sender.__name__
        logger.debug(f"Updating achievement for child: {child.childID}, content type: {content_type}")

        # Determine the achievement type based on content type and material type
        if content_type == 'ChildEduMaterial':
            material_type = instance.eduMaterial.type
            achievement_type = CONTENT_TYPE_TO_ACHIEVEMENT_TYPE.get(content_type, {}).get(material_type)
        else:
            achievement_type = CONTENT_TYPE_TO_ACHIEVEMENT_TYPE.get(content_type)

        if not achievement_type:
            logger.warning(f"No mapping found for content type: {content_type} with material type: {getattr(instance, 'eduMaterial', {}).get('type', 'N/A')}")
            return

        logger.debug(f"Achievement type for this content: {achievement_type}")

        # Fetch achievements matching the determined type
        achievements = Achievement.objects.filter(type=achievement_type)

        for achievement in achievements:
            try:
                logger.debug(f"Processing achievement: {achievement.achievementID} for child: {child.childID}")
                child_achievement, created_ca = ChildAchievement.objects.get_or_create(child=child, achievement=achievement)

                if child_achievement.complete:
                    logger.debug(f"Achievement {achievement.achievementID} is already completed. Skipping update.")
                    continue

                # Initialize progress_value
                progress_value = 0

                # Calculate progress based on completion metric
                if achievement.completion_metric == 'time_spent':
                    if achievement.type == 'quiz':
                        total_time_spent = ChildQuiz.objects.filter(
                            child=child,
                            quiz=achievement.quiz_title
                        ).aggregate(total_time=Sum('timeSpent'))['total_time'] or 0
                    elif achievement.type == 'video':
                        total_time_spent = ChildEduMaterial.objects.filter(
                            child=child,
                            eduMaterial__type='video',
                            eduMaterial=achievement.video_title
                        ).aggregate(total_time=Sum('timeSpent'))['total_time'] or 0
                    else:
                        total_time_spent = 0

                    # Handle timedelta if total_time_spent is returned as timedelta
                    if isinstance(total_time_spent, datetime.timedelta):
                        total_time_spent = total_time_spent.total_seconds()

                    progress_value = total_time_spent
                    logger.debug(f"Time spent (seconds): {progress_value}")

                elif achievement.completion_metric == 'score':
                    if achievement.type == 'quiz':
                        total_score = ChildQuiz.objects.filter(
                            child=child,
                            quiz=achievement.quiz_title
                        ).aggregate(total_score=Sum('score'))['total_score'] or 0
                        progress_value = total_score
                        logger.debug(f"Total score: {progress_value}")
                    else:
                        logger.warning(f"Score metric is not applicable for achievement type: {achievement.type}")
                        continue  # Skip if score metric is not applicable

                elif achievement.completion_metric == 'explore':
                    if achievement.type in ['book', 'video']:
                        if achievement.type == 'book':
                            unique_books = ChildEduMaterial.objects.filter(
                                child=child,
                                eduMaterial__type='book'
                            ).values('eduMaterial').distinct().count()
                            progress_value = unique_books
                            logger.debug(f"Unique books accessed: {unique_books}")
                        elif achievement.type == 'video':
                            unique_videos = ChildEduMaterial.objects.filter(
                                child=child,
                                eduMaterial__type='video'
                            ).values('eduMaterial').distinct().count()
                            progress_value = unique_videos
                            logger.debug(f"Unique videos accessed: {unique_videos}")
                    elif achievement.type == 'game':
                        unique_games = ChildGame.objects.filter(
                            child=child
                        ).values('game').distinct().count()
                        progress_value = unique_games
                        logger.debug(f"Unique games accessed: {unique_games}")
                    elif achievement.type == 'quiz':
                        unique_quizzes = ChildQuiz.objects.filter(
                            child=child
                        ).values('quiz').distinct().count()
                        progress_value = unique_quizzes
                        logger.debug(f"Unique quizzes accessed: {unique_quizzes}")
                    else:
                        logger.warning(f"'explore' metric is not defined for achievement type: {achievement.type}")
                        continue  # Skip if 'explore' metric is not defined for this type

                else:
                    logger.warning(f"Unknown completion metric: {achievement.completion_metric}")
                    continue  # Skip unknown metrics

                # Calculate completion percentage
                if achievement.criteria > 0:
                    capped_progress = min(progress_value, achievement.criteria)
                    completion_percentage = (capped_progress / achievement.criteria) * 100
                else:
                    completion_percentage = 0

                logger.debug(f"Progress Value: {progress_value}, Capped Progress: {capped_progress if achievement.criteria > 0 else 0}, Completion Percentage: {completion_percentage}")

                # Update child achievement progress
                child_achievement.progress_value = capped_progress if achievement.criteria > 0 else progress_value
                child_achievement.complete = completion_percentage >= 100
                child_achievement.save()

                logger.debug(f"Child Achievement Updated: {child_achievement.childAchievementID}, Completion Percentage: {completion_percentage}")

            except Exception as e:
                logger.error(f"Error processing achievement {achievement.achievementID} for child {child.childID}: {e}")

    except Exception as e:
        logger.error(f"Error in update_child_achievement signal: {e}")
