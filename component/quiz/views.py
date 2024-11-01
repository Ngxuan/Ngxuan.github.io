from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
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


def save_quiz_result(request):
    """
    Save the quiz result for the given child quiz.
    If the child quiz does not exist, create it first and then save the result.
    """
    if request.method == 'POST':
        try:
            # Retrieve the quiz result data from the request body
            data = json.loads(request.body)
            print(f"Request Data: {data}")  # Debugging statement to print the incoming data

            # Retrieve childID and quizID from the request data
            child_id_str = data.get('childID')  # Retrieve childID from request body
            quiz_id_str = data.get('quizID')  # Retrieve quizID from request body
            score = data.get('score', 0)  # Default to 0 if not provided
            correct_answers = data.get('correct_answers', 0)  # Default to 0 if not provided

            if not child_id_str or not quiz_id_str:
                return JsonResponse({'error': 'Missing child or quiz ID'}, status=400)

            # Convert string IDs to UUID objects
            try:
                child_id = uuid.UUID(child_id_str)  # Use the correct UUID conversion for childID
                quiz_id = uuid.UUID(quiz_id_str)  # Use the correct UUID conversion for quizID
                print(f"Converted UUIDs - Child ID: {child_id}, Quiz ID: {quiz_id}")  # Debugging statement
            except ValueError:
                return JsonResponse({'error': 'Invalid UUID format for childID or quizID'}, status=400)

            # Check if the child exists using the `childID` field, not the default `id`
            child = Child.objects.filter(childID=child_id).first()
            if not child:
                print(f"No child found with childID: {child_id}")  # Debugging statement
                return JsonResponse({'error': f'No Child matches the given query: {child_id}'}, status=400)

            # Check if the quiz exists
            quiz = Quiz.objects.filter(quizID=quiz_id).first()
            if not quiz:
                print(f"No quiz found with quizID: {quiz_id}")  # Debugging statement
                return JsonResponse({'error': f'No Quiz matches the given query: {quiz_id}'}, status=400)

            # Retrieve or create the ChildQuiz instance using UUIDs
            child_quiz, created = ChildQuiz.objects.get_or_create(
                child=child,
                quiz=quiz,
                defaults={'status': False, 'startDate': timezone.now()}
            )

            # Update the ChildQuiz instance with the quiz result
            child_quiz.score = score
            child_quiz.correct_answers = correct_answers
            child_quiz.status = True
            child_quiz.timeSpent = timezone.now() - child_quiz.startDate
            child_quiz.save()

            return JsonResponse({'message': 'Quiz result saved successfully'})
        except Exception as e:
            print(f"Error saving quiz result: {e}")  # Print the error for debugging
            return JsonResponse({'error': 'Failed to save quiz result'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)


