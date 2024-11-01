from django.shortcuts import render
from django.http import JsonResponse
from component.eduMaterial.models import EducationalMaterial
from component.quiz.models import Quiz
from component.game.models import Game
from component.user.models import Child
from component.achievement.models import Achievement, ChildAchievement
import uuid

def library(request):
    """Render the library page and handle filtering based on categories."""
    category = request.GET.get('category', 'all')  # Get category from query parameters, default to 'all'
    child_id = request.GET.get('childID', None)  # Get the child ID from query parameters
    print("Retrieved Child ID from query parameters:", child_id)  # Debugging line

    try:
        child_id = uuid.UUID(child_id) if child_id else None
    except ValueError:
        child_id = None

    filtered_content = []

    # Filter content based on the selected category
    if category == 'book':
        filtered_content = EducationalMaterial.objects.filter(type='book')
    elif category == 'video':
        filtered_content = EducationalMaterial.objects.filter(type='video')
    elif category == 'quiz':
        # Retrieve quizzes from the Quiz model instead of EducationalMaterial
        filtered_content = Quiz.objects.all()
    elif category == 'game':
        if child_id:
            print("Child ID:", child_id)  # Debugging: check the child_id

            # Retrieve the child using childID
            child = Child.objects.filter(childID=child_id).first()
            print("Fetched Child:", child)  # Debugging: check if child was fetched

            # Ensure the child exists and has an associated parent
            if child and child.parent:
                parent = child.parent  # Get the parent from the child
                print("Parent Name:", parent.name)  # Debugging: print parent's name

                # Check if the parent has an active subscription
                subscription = getattr(parent, 'subscription', None)  # Safely get subscription if it exists
                has_active_subscription = subscription.is_active() if subscription else False

                if has_active_subscription:
                    # Parent has an active subscription, child can access all active games
                    filtered_content = Game.objects.filter(status=True)
                else:
                    # Parent does not have an active subscription, child can access only free and active games
                    filtered_content = Game.objects.filter(status=True, free=True)
            else:
                print("Child not found or no parent associated.")  # Debugging message if child not linked correctly
                filtered_content = Game.objects.filter(status=True, free=True)
        else:
            print("No child_id provided.")  # Debugging: if child_id is not provided
            filtered_content = Game.objects.filter(status=True, free=True)

    elif category == 'achievement':
        # Retrieve achievements based on the child ID, if provided
        if child_id:
            child = Child.objects.filter(childID=child_id).first()
            if child:
                # Retrieve ChildAchievement instances and their related Achievement data
                filtered_content = ChildAchievement.objects.filter(child=child).select_related('achievement')
            else:
                # If no child is found, show all available achievements
                filtered_content = Achievement.objects.all()
        else:
            # If no child ID is provided, show all available achievements
            filtered_content = Achievement.objects.all()
    else:
        # If no category matches, default to all items in the EducationalMaterial model
        filtered_content = EducationalMaterial.objects.all()

    # Check if the request is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if category == 'quiz':
            content_list = list(filtered_content.values('quizID', 'title', 'thumbnail_url'))
        elif category == 'game':
            content_list = list(filtered_content.values('gameID', 'title', 'thumbnail_url'))
        elif category == 'achievement':
            # Format the achievements data for AJAX response
            content_list = list(filtered_content.values('achievementID', 'title', 'description', 'thumbnail_url'))
        else:
            content_list = list(filtered_content.values('eduMaterialID', 'title', 'file_url', 'thumbnail_url', 'type'))

        return JsonResponse({'content': content_list}, safe=False)

    return render(request, 'childHome.html', {'materials': filtered_content, 'selected_category': category})
