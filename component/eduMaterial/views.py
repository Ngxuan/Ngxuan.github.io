# component/eduMaterial/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import ChildEduMaterial, EducationalMaterial
from component.user.models import Child
from django.views.decorators.csrf import csrf_exempt
import uuid
import json
from datetime import timedelta

def book_viewer(request, childID, eduMaterialID):
    # Get the book URL from the query parameter 'bookUrl'
    book_url = request.GET.get('bookUrl', '')

    # Retrieve the EducationalMaterial object using eduMaterialID
    book = get_object_or_404(EducationalMaterial, eduMaterialID=eduMaterialID)

    # Render the 'book.html' template and pass the book_url as context
    return render(request, 'book.html', {'book_url': book_url, 'childID': childID, 'eduMaterialID': eduMaterialID, 'book_title': book.title})

from django.utils import timezone



@csrf_exempt
def record_time_spent(request, childID, eduMaterialID):
    """
    Records the time spent on any educational material (video or book) for a child.
    """
    if request.method == 'POST':
        try:
            print(f"Received request to record time. Child ID: {childID}, EduMaterial ID: {eduMaterialID}")

            # Retrieve the child and educational material objects using their unique IDs
            child = Child.objects.get(childID=childID)
            edu_material = EducationalMaterial.objects.get(eduMaterialID=eduMaterialID)

            print(f"Child: {child}, Educational Material: {edu_material}")

            # Check if the material is a book or a video
            material_type = edu_material.type
            print(f"Recording time spent for a {material_type}.")  # For logging purposes

            # Get the time spent value from the POST data and ensure it is an integer (representing seconds)
            data = json.loads(request.body)
            print(f"Request Data: {data}")  # Print request data for debugging

            # Extract time spent from the request and convert to integer
            time_spent_seconds = int(data.get('timeSpent', 0))
            print(f"Time spent (in seconds): {time_spent_seconds}")

            # Convert the time spent in seconds to a timedelta object
            time_spent_duration = timedelta(seconds=time_spent_seconds)
            print(f"Time spent duration: {time_spent_duration}")

            # Check if a record already exists for this child and educational material
            child_edu_material = ChildEduMaterial.objects.filter(child=child, eduMaterial=edu_material).first()
            print(f"Existing ChildEduMaterial: {child_edu_material}")

            # If no record exists, create a new one with a unique ID and initialize timeSpent with 0 duration
            if not child_edu_material:
                child_edu_material = ChildEduMaterial.objects.create(
                    childEduMaterialID=str(uuid.uuid4()),
                    child=child,
                    eduMaterial=edu_material,
                    timeSpent=timedelta(0)  # Initialize with zero duration
                )
                print("Created new ChildEduMaterial record.")

            # Accumulate the time spent using timedelta arithmetic
            child_edu_material.timeSpent += time_spent_duration
            child_edu_material.save()

            # Return the total time spent in seconds (converted back from timedelta)
            total_time_spent_seconds = child_edu_material.timeSpent.total_seconds()
            print(f"Total time spent (in seconds): {total_time_spent_seconds}")

            return JsonResponse({'status': 'success', 'totalTimeSpent': total_time_spent_seconds})

        except Child.DoesNotExist:
            print("Error: Child not found.")
            return JsonResponse({'status': 'error', 'message': 'Child not found.'}, status=404)

        except EducationalMaterial.DoesNotExist:
            print("Error: Educational material not found.")
            return JsonResponse({'status': 'error', 'message': 'Educational material not found.'}, status=404)

        except Exception as e:
            print(f"Unexpected error: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)