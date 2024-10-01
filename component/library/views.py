from django.shortcuts import render
from django.http import JsonResponse
from component.eduMaterial.models import EducationalMaterial
from component.quiz.models import Quiz  # Import the Quiz model

def library(request):
    """Render the library page and handle filtering based on categories."""
    category = request.GET.get('category', 'all')  # Get category from query parameters, default to 'all'
    filtered_content = []

    # Filter content based on the selected category
    if category == 'book':
        filtered_content = EducationalMaterial.objects.filter(type='book')
    elif category == 'video':
        filtered_content = EducationalMaterial.objects.filter(type='video')
    elif category == 'quiz':
        # Retrieve quizzes from the Quiz model instead of EducationalMaterial
        filtered_content = Quiz.objects.all()
    else:
        # If no category matches, default to all items in the EducationalMaterial model
        filtered_content = EducationalMaterial.objects.all()

    # Check if the request is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if category == 'quiz':
            # If the category is quiz, format the quiz data to return as JSON
            content_list = list(filtered_content.values('quizID', 'title', 'thumbnail_url'))  # Adjust fields based on Quiz model
        else:
            # For books and videos, use the EducationalMaterial fields
            content_list = list(filtered_content.values('eduMaterialID', 'title', 'file_url', 'thumbnail_url', 'type'))

        # Return the JSON response with content list
        return JsonResponse({'content': content_list}, safe=False)

    # Render the library template with the filtered content for normal (non-AJAX) requests
    return render(request, 'childHome.html', {'materials': filtered_content, 'selected_category': category})
