from django.shortcuts import render
from django.http import JsonResponse
from component.eduMaterial.models import EducationalMaterial
from component.quiz.models import Quiz
from component.game.models import Game
from component.user.models import Child
from component.achievement.models import Achievement, ChildAchievement
import uuid
import logging
import os
import fitz  # PyMuPDF for PDF text extraction
from django.http import JsonResponse, HttpResponse
from django.views import View
from resemble import Resemble
from django.core.files.temp import NamedTemporaryFile

# books/views.py
import fitz  # PyMuPDF for PDF text extraction
import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from resemble import Resemble
import json



def library(request):
    """Render the library page and handle filtering based on categories."""
    category = request.GET.get('category', 'all')  # Get category from query parameters, default to 'all'
    child_id = request.GET.get('childID', None)  # Get the child ID from query parameters
    print("Retrieved Child ID from query parameters:", child_id)  # Debugging line

    try:
        child_id = uuid.UUID(child_id) if child_id else None
    except ValueError:
        child_id = None

    filtered_content = []

    # Filter content based on the selected category
    if category == 'book':
        filtered_content = EducationalMaterial.objects.filter(type='book')
    elif category == 'video':
        filtered_content = EducationalMaterial.objects.filter(type='video')
    elif category == 'quiz':
        # Retrieve quizzes from the Quiz model instead of EducationalMaterial
        filtered_content = Quiz.objects.all()
    elif category == 'game':
        if child_id:
            print("Child ID:", child_id)  # Debugging: check the child_id

            # Retrieve the child using childID
            child = Child.objects.filter(childID=child_id).first()
            print("Fetched Child:", child)  # Debugging: check if child was fetched

            # Ensure the child exists and has an associated parent
            if child and child.parent:
                parent = child.parent  # Get the parent from the child
                print("Parent Name:", parent.name)  # Debugging: print parent's name

                # Check if the parent has an active subscription
                subscription = getattr(parent, 'subscription', None)  # Safely get subscription if it exists
                has_active_subscription = subscription.is_active() if subscription else False

                if has_active_subscription:
                    # Parent has an active subscription, child can access all active games
                    filtered_content = Game.objects.filter(status=True)
                else:
                    # Parent does not have an active subscription, child can access only free and active games
                    filtered_content = Game.objects.filter(status=True, free=True)
            else:
                print("Child not found or no parent associated.")  # Debugging message if child not linked correctly
                filtered_content = Game.objects.filter(status=True, free=True)
        else:
            print("No child_id provided.")  # Debugging: if child_id is not provided
            filtered_content = Game.objects.filter(status=True, free=True)

    elif category == 'achievement':
        # Retrieve achievements based on the child ID, if provided
        if child_id:
            child = Child.objects.filter(childID=child_id).first()
            if child:
                # Retrieve ChildAchievement instances and their related Achievement data
                filtered_content = ChildAchievement.objects.filter(child=child).select_related('achievement')
            else:
                # If no child is found, show all available achievements
                filtered_content = Achievement.objects.all()
        else:
            # If no child ID is provided, show all available achievements
            filtered_content = Achievement.objects.all()
    else:
        # If no category matches, default to all items in the EducationalMaterial model
        filtered_content = EducationalMaterial.objects.all()

    # Check if the request is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if category == 'quiz':
            content_list = list(filtered_content.values('quizID', 'title', 'thumbnail_url'))
        elif category == 'game':
            content_list = list(filtered_content.values('gameID', 'title', 'thumbnail_url'))
        elif category == 'achievement':
            # Format the achievements data for AJAX response
            content_list = list(filtered_content.values('achievementID', 'title', 'description', 'thumbnail_url'))
        else:
            content_list = list(filtered_content.values('eduMaterialID', 'title', 'file_url', 'thumbnail_url', 'type'))

        return JsonResponse({'content': content_list}, safe=False)

    return render(request, 'childHome.html', {'materials': filtered_content, 'selected_category': category})


logger = logging.getLogger(__name__)

# Azure TTS API configurations
AZURE_TTS_KEY = os.getenv('AZURE_TTS_KEY', '8xgC0N0p6m1ynBqw11zDkdssqWprB7LSRpCd1IvqW4jASLPlFjIxJQQJ99AKACHYHv6XJ3w3AAAYACOGS9vE')
AZURE_REGION = os.getenv('AZURE_REGION', 'eastus2')
TOKEN_URL = f'https://{AZURE_REGION}.api.cognitive.microsoft.com/sts/v1.0/issueToken'
TTS_URL = f'https://{AZURE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1'


def get_azure_access_token():
    headers = {'Ocp-Apim-Subscription-Key': AZURE_TTS_KEY}
    response = requests.post(TOKEN_URL, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        logger.error(f"Failed to get token: {response.status_code} - {response.text}")
        return None


def azure_text_to_speech(text, voice_name="en-US-JennyNeural"):
    token = get_azure_access_token()
    if not token:
        return None

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'audio-24khz-48kbitrate-mono-mp3'
    }

    ssml = f"""
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
        <voice name='{voice_name}'>{text}</voice>
    </speak>
    """

    response = requests.post(TTS_URL, headers=headers, data=ssml)
    if response.status_code == 200:
        return response.content  # Return the raw audio data
    else:
        logger.error(f"TTS request failed: {response.status_code} - {response.text}")
        return None


@csrf_exempt
def pdf_to_tts_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            if not text:
                return JsonResponse({'error': 'No text provided for TTS'}, status=400)

            # Generate TTS audio and return it as a stream
            audio_data = azure_text_to_speech(text)
            if audio_data:
                response = HttpResponse(audio_data, content_type='audio/mpeg')
                response['Content-Disposition'] = 'inline; filename="tts_audio.mp3"'
                return response
            else:
                return JsonResponse({'error': 'Failed to generate TTS'}, status=500)

        except Exception as e:
            logger.exception("An error occurred during TTS generation")
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)