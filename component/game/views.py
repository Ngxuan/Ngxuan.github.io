# views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
import json
import uuid
from .models import Game, ChildGame, GameType, GameQuestion, GameQuestionOption
from component.user.models import Child

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
    if game.type.type_name == 'Drag and Drop':
        template = 'drag_and_drop.html'
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
        'questions_with_options': questions_with_options,
    }
    return render(request, template, context)


def save_game_result(request):
    """
    Save the game result for the given child game.
    If the child game does not exist, create it first and then save the result.
    """
    if request.method == 'POST':
        try:
            # Retrieve the game result data from the request body
            data = json.loads(request.body)
            print(f"Request Data: {data}")  # Debugging statement to print the incoming data

            # Retrieve childID and gameID from the request data
            child_id_str = data.get('childID')  # Retrieve childID from request body
            game_id_str = data.get('gameID')  # Retrieve gameID from request body
            time_spent = data.get('timeSpent', 0)  # Default to 0 if not provided

            if not child_id_str or not game_id_str:
                return JsonResponse({'error': 'Missing child or game ID'}, status=400)

            # Convert string IDs to UUID objects
            try:
                child_id = uuid.UUID(child_id_str)  # Use the correct UUID conversion for childID
                game_id = uuid.UUID(game_id_str)  # Use the correct UUID conversion for gameID
                print(f"Converted UUIDs - Child ID: {child_id}, Game ID: {game_id}")  # Debugging statement
            except ValueError:
                return JsonResponse({'error': 'Invalid UUID format for childID or gameID'}, status=400)

            # Check if the child exists using the childID field, not the default id
            child = Child.objects.filter(childID=child_id).first()
            if not child:
                print(f"No child found with childID: {child_id}")  # Debugging statement
                return JsonResponse({'error': f'No Child matches the given query: {child_id}'}, status=400)

            # Check if the game exists
            game = Game.objects.filter(gameID=game_id).first()
            if not game:
                print(f"No game found with gameID: {game_id}")  # Debugging statement
                return JsonResponse({'error': f'No Game matches the given query: {game_id}'}, status=400)

            # Retrieve or create the ChildGame instance using UUIDs
            child_game, created = ChildGame.objects.get_or_create(
                child=child,
                game=game,
                defaults={'playDate': timezone.now(), 'timeSpent': timezone.now() - timezone.now()}  # Set default values
            )

            # Update the ChildGame instance with the game result

            child_game.timeSpent = timezone.timedelta(seconds=time_spent)  # Convert time spent to timedelta
            child_game.save()

            return JsonResponse({'message': 'Game result saved successfully'})
        except Exception as e:
            print(f"Error saving game result: {e}")  # Print the error for debugging
            return JsonResponse({'error': 'Failed to save game result'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)
