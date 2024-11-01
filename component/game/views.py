# views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
from .models import Child, Game, ChildGame
import uuid
import json

# views.py
def play_game(request, child_id, game_id):
    """
    View to render the appropriate game template based on the game type.
    """
    # Fetch the game object using its ID
    game = get_object_or_404(Game, pk=game_id)

    # Prepare the game questions and options, including the correct option ID
    questions_with_options = [
        {
            'question': question,
            'options': question.options.all(),
            'correct_option_id': question.options.filter(is_correct=True).first().optionID  # Fetch the correct option ID for each question
        }
        for question in game.questions.all()
    ]

    # Determine which template to use based on the game's type
    if game.type.type_name == 'drag':
        template = 'gameDrag.html'
    elif game.type.type_name == 'matching':
        template = 'gameMatch.html'
    elif game.type.type_name == 'Multiple Choice':
        template = 'multiple_choice.html'
    else:
        template = 'default_game_template.html'  # Fallback template for other games

    # Render the selected template with the game, child game, and questions context
    context = {
        'game': game,
        'childID': child_id,
        'gameID': game_id,
        'questions_with_options': questions_with_options,
    }
    return render(request, template, context)


@csrf_exempt
def record_game_time_spent(request, childID, gameID):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body.decode('utf-8'))
            time_spent_seconds = data.get('timeSpent', 0)
            attempts = data.get('attempts', 0)

            # Retrieve the child and game using their unique IDs
            child = get_object_or_404(Child, childID=childID)
            game = get_object_or_404(Game, gameID=gameID)

            # Convert the time spent in seconds to a timedelta object
            time_spent_duration = timedelta(seconds=int(time_spent_seconds))

            # Check if a record already exists for this child and game
            child_game, created = ChildGame.objects.get_or_create(
                child=child, game=game,
                defaults={'childGameID': str(uuid.uuid4()), 'timeSpent': timedelta(0)}
            )

            # If the record already exists, accumulate the time spent
            if not created:
                child_game.timeSpent += time_spent_duration
            else:
                child_game.timeSpent = time_spent_duration

            # Save the child game record
            child_game.save()

            # Return the total time spent in seconds (converted back from timedelta)
            total_time_spent_seconds = child_game.timeSpent.total_seconds()
            return JsonResponse({'status': 'success', 'totalTimeSpent': total_time_spent_seconds})

        except Child.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Child not found.'}, status=404)

        except Game.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Game not found'}, status=404)


def game_detail(request, game_id):
    # Retrieve the game object by ID
    game = get_object_or_404(Game, gameID=game_id)

    # Pass the game object to the template for rendering
    context = {
        'game': game
    }
    return render(request, 'gameDetail.html', context)