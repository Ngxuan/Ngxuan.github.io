# eduMaterial/views.py

from django.shortcuts import render
from django.http import JsonResponse
from component.eduMaterial.models import EducationalMaterial

def library(request):
    """Render the library page and handle filtering based on categories."""
    category = request.GET.get('category', 'all')  # Get category from query parameters, default to 'all'
    filtered_content = []

    # Filter content based on the selected category
    if category == 'book':
        filtered_content = EducationalMaterial.objects.filter(type='book')
    elif category == 'video':
        filtered_content = EducationalMaterial.objects.filter(type='video')
    else:
        # If no category matches, default to all items in the model
        filtered_content = EducationalMaterial.objects.all()

    # Check if the request is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Convert the queryset to a list of dictionaries for JSON response
        # Use 'eduMaterialID' instead of 'id'
        content_list = list(filtered_content.values('eduMaterialID', 'title', 'file_url'))
        return JsonResponse({'content': content_list})

    # Render the library template with the filtered content for normal (non-AJAX) requests
    return render(request, 'childHome.html', {'materials': filtered_content, 'selected_category': category})
