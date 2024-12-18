from datetime import timedelta

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Quiz, ChildQuiz, ChildQuizLog
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
    if request.method == 'POST':
        try:
            # Parse and log incoming data
            data = json.loads(request.body.decode('utf-8'))
            print(f"Received data: {data}")

            # Extract values from the request
            score = data.get('score', 0)
            correct_answers = data.get('correct_answers', 0)
            time_spent_seconds = data.get('timeSpent', 0)  # Time spent is directly received
            print(f"timeSpent (seconds) received: {time_spent_seconds}")

            # Validate child and quiz IDs
            child_id_str = data.get('childID')
            quiz_id_str = data.get('quizID')

            if not child_id_str or not quiz_id_str:
                return JsonResponse({'error': 'Missing child or quiz ID'}, status=400)

            try:
                child_id = uuid.UUID(child_id_str)
                quiz_id = uuid.UUID(quiz_id_str)
            except ValueError:
                return JsonResponse({'error': 'Invalid UUID format for childID or quizID'}, status=400)

            # Fetch child and quiz objects
            child = get_object_or_404(Child, childID=child_id)
            quiz = get_object_or_404(Quiz, quizID=quiz_id)

            # Convert time spent to timedelta
            time_spent_duration = timedelta(seconds=int(time_spent_seconds))
            print(f"timeSpent duration created: {time_spent_duration}")

            # Retrieve or create the ChildQuiz object
            child_quiz, created = ChildQuiz.objects.get_or_create(
                child=child,
                quiz=quiz,
                defaults={
                    'childQuizID': str(uuid.uuid4()),
                    'timeSpent': time_spent_duration or timedelta(seconds=0)  # Initialize with current time spent
                }
            )

            if created:
                print(f"ChildQuiz created with timeSpent: {child_quiz.timeSpent}")
            else:
                print(f"ChildQuiz found. Current timeSpent: {child_quiz.timeSpent}")
                if child_quiz.timeSpent is None:
                    child_quiz.timeSpent = timedelta(seconds=0)  # Ensure it starts from 0 if not initialized
                child_quiz.timeSpent += time_spent_duration  # Accumulate the new time spent
                print(f"Updated timeSpent: {child_quiz.timeSpent}")

            # Update quiz results
            child_quiz.score = score
            child_quiz.correct_answers = correct_answers
            child_quiz.status = True

            # Save the ChildQuiz object
            try:
                child_quiz.save()
                print(f"Final saved timeSpent: {child_quiz.timeSpent}")
            except Exception as e:
                print(f"Error saving ChildQuiz: {e}")
                return JsonResponse({'status': 'error', 'message': 'Failed to save ChildQuiz object'}, status=500)

            # Create a log entry in ChildQuizLog
            child_quiz_log = ChildQuizLog.objects.create(
                childQuizLogID=str(uuid.uuid4()),
                child=child,
                quiz=quiz,
                time_spent=time_spent_duration,
                access_date=timezone.now()  # Log the exact date and time of the quiz access
            )
            print(f"ChildQuizLog created: {child_quiz_log}")

            # Return the total accumulated time spent in seconds
            total_time_spent_seconds = child_quiz.timeSpent.total_seconds()

            return JsonResponse({
                'status': 'success',
                'message': 'Quiz result saved successfully',
                'timeSpent': total_time_spent_seconds
            })

        except Exception as e:
            print(f"Error saving quiz result: {e}")
            return JsonResponse({'status': 'error', 'message': 'Failed to save quiz result'}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

