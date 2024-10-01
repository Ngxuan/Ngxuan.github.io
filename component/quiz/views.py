from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Quiz, ChildQuiz
import json
from django.db import DataError


def quiz_page(request, childID, quizID):
    """Display the quiz page based on the selected quiz."""
    try:
        # Retrieve the quiz using the quizID with efficient related object fetching
        quiz = Quiz.objects.prefetch_related('questions__options').get(quizID=quizID)

        # Prepare questions with correct option ID
        questions_with_correct_option = []
        for question in quiz.questions.all():
            correct_option = question.options.filter(is_correct=True).first()  # Get the correct option for each question
            questions_with_correct_option.append({
                'question': question,
                'correct_option_id': correct_option.optionID if correct_option else None
            })

        # Pass the modified questions list to the template
        return render(request, 'quiz.html', {
            'quiz': quiz,
            'childID': childID,
            'questions_with_correct_option': questions_with_correct_option
        })
    except Quiz.DoesNotExist:
        return JsonResponse({'error': 'Quiz not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


def save_quiz_result(request):
    """Save the quiz results for a child."""
    if request.method == 'POST':
        try:
            # Parse the request data (assumed to be JSON)
            data = json.loads(request.body)

            # Retrieve the necessary data from the request
            child_quiz_id = data.get('child_quiz_id')
            correct_answers = data.get('correct_answers')
            total_questions = data.get('total_questions')

            # Validate that the necessary fields are present
            if not child_quiz_id or correct_answers is None or total_questions is None:
                return JsonResponse({'error': 'Invalid data provided'}, status=400)

            # Retrieve the `ChildQuiz` instance using the provided child_quiz_id
            child_quiz = get_object_or_404(ChildQuiz, childQuizID=child_quiz_id)

            # Calculate the score as a percentage of correct answers out of total questions
            if total_questions > 0:
                score = (correct_answers / total_questions) * 100
            else:
                score = 0  # Handle division by zero

            # Validate and adjust the score if necessary
            score = max(0, min(score, 100))  # Ensure the score is between 0 and 100

            # Update and save the `ChildQuiz` instance
            child_quiz.score = score
            child_quiz.correct_answers = correct_answers
            child_quiz.status = True  # Mark the quiz as completed
            child_quiz.save()

            return JsonResponse({'message': 'Quiz result saved successfully', 'score': score})
        except ChildQuiz.DoesNotExist:
            return JsonResponse({'error': 'Child quiz not found'}, status=404)
        except DataError:
            return JsonResponse({'error': 'Failed to save quiz result due to data error'}, status=500)
        except Exception as e:
            return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
