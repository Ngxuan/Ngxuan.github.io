from django.shortcuts import render
from django.http import JsonResponse
from component.eduMaterial.models import EducationalMaterial
import logging
import os
import requests
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import render
import uuid
from component.user.models import Child
from component.achievement.models import Achievement, ChildAchievement
from component.eduMaterial.models import EducationalMaterial
from component.quiz.models import Quiz
from component.game.models import Game
from django.db.models import OuterRef, Subquery, Case, When, Value, BooleanField,  F


def library(request):
    """Render the library page and handle filtering based on categories."""
    category = request.GET.get('category', 'all')  # Default to 'all' if no category specified
    child_id = request.GET.get('childID')  # Retrieve child ID if available
    print("Retrieved Child ID:", child_id)  # Debugging line

    try:
        child_id = uuid.UUID(child_id) if child_id else None
    except ValueError:
        child_id = None

    filtered_content = []

    # Determine content based on category
    if category == 'book':
        filtered_content = EducationalMaterial.objects.filter(type='book')
    elif category == 'video':
        filtered_content = EducationalMaterial.objects.filter(type='video')
    elif category == 'quiz':
        filtered_content = Quiz.objects.all()
    elif category == 'game':
        filtered_content = fetch_games(child_id)
    elif category == 'achievement':
        filtered_content = fetch_achievements(child_id)

    # Check if request is AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        content_list = generate_content_list(category, filtered_content)
        return JsonResponse({'content': content_list}, safe=False)

    # Render template for non-AJAX requests
    return render(request, 'childHome.html', {'materials': filtered_content, 'selected_category': category})

def fetch_games(child_id):
    """Fetch games based on child ID and subscription status."""
    if child_id:
        child = Child.objects.filter(childID=child_id).first()
        print("Fetched Child:", child)  # Debugging line
        if child and child.parent:
            parent = child.parent
            print("Parent Name:", parent.name)  # Debugging line
            has_active_subscription = getattr(parent, 'subscription', None) and parent.subscription.is_active()
            return Game.objects.filter(status=True) if has_active_subscription else Game.objects.filter(status=True, free=True)
    print("No valid child or parent subscription. Access limited to free games.")
    return Game.objects.filter(status=True, free=True)


def fetch_achievements(child_id):
    """Fetch achievements with child's completion status and include formatted criteria if time spent is the metric."""
    achievements = Achievement.objects.all()

    if child_id:
        child = Child.objects.filter(childID=child_id).first()

        if child:
            # Query to get relevant ChildAchievement data for progress value
            child_achievement_qs = ChildAchievement.objects.filter(
                child=child,
                achievement=OuterRef('pk')
            )

            achievements = achievements.annotate(
                completed=Case(
                    When(
                        pk__in=Subquery(child_achievement_qs.filter(complete=True).values('achievement')),
                        then=Value(True)
                    ),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
                currentValue=Subquery(child_achievement_qs.values('progress_value')[:1]),
                targetValue=F('criteria')
            )


    return achievements

def format_time(seconds):
    """Convert seconds to a string in 'X hours Y minutes' format."""
    total_minutes = int(seconds / 60)  # Convert seconds to minutes
    hours_part = total_minutes // 60
    minutes_part = total_minutes % 60
    return f"{hours_part} hrs {minutes_part} mins" if hours_part > 0 else f"{minutes_part} mins"


def generate_content_list(category, filtered_content):
    """Generate content list based on category for AJAX requests."""
    content_list = []

    if category == 'quiz':
        return list(filtered_content.values('quizID', 'title', 'thumbnail_url'))
    elif category == 'game':
        return list(filtered_content.values('gameID', 'title', 'thumbnail_url'))
    elif category == 'achievement':
        if isinstance(filtered_content.first(), Achievement):
            for achievement in filtered_content:
                item = {
                    'achievementID': achievement.achievementID,
                    'title': achievement.title,
                    'description': achievement.description,
                    'thumbnail_url': achievement.thumbnail_url,
                    'completed': achievement.completed,
                    'currentValue': achievement.currentValue,
                    'targetValue': achievement.targetValue,
                    'completionMetric' : achievement.completion_metric
                }
                # Conditionally format criteria for time_spent metric
                if achievement.completion_metric == 'time_spent':
                    item['formattedCriteria'] = format_time(achievement.criteria)
                else:
                    item['formattedCriteria'] = str(achievement.criteria)

                content_list.append(item)
    else:
        return list(filtered_content.values('eduMaterialID', 'title', 'file_url', 'thumbnail_url', 'type'))

    return content_list


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