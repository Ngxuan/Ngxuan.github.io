from django.shortcuts import render
from django.http import JsonResponse
from component.eduMaterial.models import EducationalMaterial
from component.quiz.models import Quiz  # Import the Quiz model
from component.game.models import Game  # Import the Game model
from component.user.models import Child, Parent  # Import the Child and Parent models
from component.game.models import GamePurchase  # Import the GamePurchase model


def library(request):
    """Render the library page and handle filtering based on categories."""
    category = request.GET.get('category', 'all')  # Get category from query parameters, default to 'all'
    child_id = request.GET.get('childID', None)  # Get the child ID from query parameters

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
            # If a child ID is provided, get the child and their parent
            child = Child.objects.filter(pk=child_id).first()

            if child and child.parent:
                parent = child.parent

                # Free and active games
                free_active_games = Game.objects.filter(status=True, free=True)

                # Purchased games by this parent
                purchased_games = Game.objects.filter(
                    purchases__parent=parent
                ).distinct()

                # Combine both querysets
                filtered_content = free_active_games | purchased_games
            else:
                # If no parent or child found, just display the free and active games
                filtered_content = Game.objects.filter(status=True, free=True)
        else:
            # If no child ID is provided, display only free and active games
            filtered_content = Game.objects.filter(status=True, free=True)
    else:
        # If no category matches, default to all items in the EducationalMaterial model
        filtered_content = EducationalMaterial.objects.all()

    # Check if the request is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if category == 'quiz':
            # If the category is quiz, format the quiz data to return as JSON
            content_list = list(
                filtered_content.values('quizID', 'title', 'thumbnail_url'))  # Adjust fields based on Quiz model
        elif category == 'game':
            # If the category is game, format the game data to return as JSON
            content_list = list(
                filtered_content.values('gameID', 'title', 'thumbnail_url'))  # Adjust fields based on Game model
        else:
            # For books and videos, use the EducationalMaterial fields
            content_list = list(filtered_content.values('eduMaterialID', 'title', 'file_url', 'thumbnail_url', 'type'))

        # Return the JSON response with content list
        return JsonResponse({'content': content_list}, safe=False)

    # Render the library template with the filtered content for normal (non-AJAX) requests
    return render(request, 'childHome.html', {'materials': filtered_content, 'selected_category': category})
