from datetime import timedelta

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Quiz, ChildQuiz
import json
from django.utils import timezone
import uuid
from ..user.models import Child


def quiz_page(request, childID, quizID):
    """
    Display the quiz page based on the selected quiz.
    Do not create a ChildQuiz instance here. It will be created when the quiz is completed.
    """
    # Retrieve the quiz using the quizID
    quiz = get_object_or_404(Quiz, quizID=quizID)

    # Prepare questions with correct option ID
    questions_with_correct_option = [
        {'question': question, 'correct_option_id': question.options.filter(is_correct=True).first().optionID}
        for question in quiz.questions.all()
    ]

    # Render the quiz page with the quiz details
    return render(request, 'quiz.html', {
        'quiz': quiz,
        'childID': childID,
        'questions_with_correct_option': questions_with_correct_option
    })


@csrf_exempt
def save_quiz_result(request):
    """
    Save the quiz result and accumulate the time spent each time the quiz is answered.
    """
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body.decode('utf-8'))
            score = data.get('score', 0)  # Default to 0 if not provided
            correct_answers = data.get('correct_answers', 0)  # Default to 0 if not provided
            time_spent_seconds = data.get('timeSpent', 0)  # Time spent on this submission in seconds

            # Retrieve child and quiz using their unique IDs
            child_id_str = data.get('childID')
            quiz_id_str = data.get('quizID')

            if not child_id_str or not quiz_id_str:
                return JsonResponse({'error': 'Missing child or quiz ID'}, status=400)

            # Convert string IDs to UUID objects
            try:
                child_id = uuid.UUID(child_id_str)  # Convert childID to UUID
                quiz_id = uuid.UUID(quiz_id_str)  # Convert quizID to UUID
            except ValueError:
                return JsonResponse({'error': 'Invalid UUID format for childID or quizID'}, status=400)

            # Retrieve the child and quiz objects
            child = get_object_or_404(Child, childID=child_id)
            quiz = get_object_or_404(Quiz, quizID=quiz_id)

            # Convert the time spent in seconds to a timedelta object
            time_spent_duration = timedelta(seconds=int(time_spent_seconds))

            # Retrieve or create the ChildQuiz instance
            child_quiz, created = ChildQuiz.objects.get_or_create(
                child=child, quiz=quiz,
                defaults={'childQuizID': str(uuid.uuid4()), 'timeSpent': time_spent_duration}  # Use time_spent_duration for first access
            )

            # If the record already exists, accumulate the time spent based on the request
            if not created:
                # Add the new time spent (from the request) to the previous total time spent
                child_quiz.timeSpent += time_spent_duration

            # Update the ChildQuiz instance with quiz results
            child_quiz.score = score
            child_quiz.correct_answers = correct_answers
            child_quiz.status = True

            # Save the updated ChildQuiz instance
            child_quiz.save()

            # Return the total time spent in seconds (converted back from timedelta)
            total_time_spent_seconds = child_quiz.timeSpent.total_seconds()

            return JsonResponse({
                'status': 'success',
                'message': 'Quiz result saved successfully',
                'totalTimeSpent': total_time_spent_seconds
            })

        except Exception as e:
            print(f"Error saving quiz result: {e}")  # Print the error for debugging
            return JsonResponse({'status': 'error', 'message': 'Failed to save quiz result'}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
