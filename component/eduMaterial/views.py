# component/eduMaterial/views.py
from django.shortcuts import render, get_object_or_404
from .models import EducationalMaterial

def book_viewer(request, childID, eduMaterialID):
    # Get the book URL from the query parameter 'bookUrl'
    book_url = request.GET.get('bookUrl', '')

    # Retrieve the EducationalMaterial object using eduMaterialID
    book = get_object_or_404(EducationalMaterial, eduMaterialID=eduMaterialID)

    # Render the 'book.html' template and pass the book_url as context
    return render(request, 'book.html', {'book_url': book_url, 'childID': childID, 'eduMaterialID': eduMaterialID, 'book_title': book.title})
