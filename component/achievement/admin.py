# admin.py

from django import forms
from django.contrib import admin
from .models import Achievement, ChildAchievement
from component.supabase_client import upload_file_to_supabase
from component.quiz.models import Quiz  # Importing QuizType from the correct module
from component.eduMaterial.models import EducationalMaterial

class AchievementAdminForm(forms.ModelForm):
    upload_thumbnail = forms.FileField(required=False, label='Upload Thumbnail to Supabase')
    quiz_title = forms.ModelChoiceField(queryset=Quiz.objects.all(), required=False, label='Quiz Title')  # For quiz type
    video_title = forms.ModelChoiceField(
        queryset=EducationalMaterial.objects.filter(type='video'),
        required=False,
        label='Video Title'
    )  # For video type

    class Meta:
        model = Achievement
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(AchievementAdminForm, self).__init__(*args, **kwargs)

        # Check if the instance is already created (i.e., editing an existing achievement)
        if self.instance and self.instance.pk:
            if self.instance.type == 'quiz':
                # For quiz type
                self.fields['quiz_title'].required = True  # Make quiz_title required
                self.fields['video_title'].widget = forms.HiddenInput()  # Hide video_title field
            elif self.instance.type == 'video':
                # For video type
                self.fields['video_title'].required = True  # Make video_title required
                self.fields['quiz_title'].widget = forms.HiddenInput()  # Hide quiz_title field
            else:
                # For other types, hide both fields
                self.fields['quiz_title'].widget = forms.HiddenInput()
                self.fields['video_title'].widget = forms.HiddenInput()
        else:
            # If creating a new instance, check if type is provided in POST data
            if 'type' in self.data:
                if self.data['type'] == 'quiz':
                    self.fields['quiz_title'].required = True  # Make quiz_title required for new quizzes
                    self.fields['video_title'].widget = forms.HiddenInput()  # Hide video_title field
                elif self.data['type'] == 'video':
                    self.fields['video_title'].required = True  # Make video_title required for new videos
                    self.fields['quiz_title'].widget = forms.HiddenInput()  # Hide quiz_title field
                else:
                    # Hide both fields if type is not quiz or video
                    self.fields['quiz_title'].widget = forms.HiddenInput()
                    self.fields['video_title'].widget = forms.HiddenInput()
            else:
                # Hide both fields initially if no type is provided
                self.fields['quiz_title'].widget = forms.HiddenInput()
                self.fields['video_title'].widget = forms.HiddenInput()


# Create the Achievement admin class with support for Supabase uploads
class AchievementAdmin(admin.ModelAdmin):
    form = AchievementAdminForm
    list_display = ('title', 'description', 'criteria', 'status', 'thumbnail_url', 'type', 'completion_metric')
    list_filter = ('status', 'type', 'completion_metric')  # Add filters for type and completion_metric
    search_fields = ('title', 'description')
    fields = ('title', 'description', 'criteria', 'status', 'thumbnail_url', 'upload_thumbnail', 'type', 'quiz_title','video_title', 'completion_metric')  # Include quiz_type in fields
    readonly_fields = ('thumbnail_url',)  # Make thumbnail_url readonly

    def save_model(self, request, obj, form, change):
        """
        Override save_model to handle thumbnail uploads to Supabase storage.
        """
        uploaded_thumbnail = form.cleaned_data.get('upload_thumbnail')

        # Define the bucket name for thumbnails
        bucket_name = 'fyp'  # Set this to your actual bucket name

        # Handle thumbnail upload
        if uploaded_thumbnail:
            try:
                # Read the content of the uploaded thumbnail
                thumbnail_content = uploaded_thumbnail.read()  # Read the thumbnail content as bytes

                # Use 'achievement' as the category for thumbnails
                thumbnail_category = 'achievement'

                # Log the thumbnail information for debugging
                print(f"Uploading thumbnail: {uploaded_thumbnail.name}, Content length: {len(thumbnail_content)} bytes, Category: {thumbnail_category}")

                # Upload the thumbnail to Supabase storage and get the public URL
                thumbnail_url = upload_file_to_supabase(bucket_name, thumbnail_content, uploaded_thumbnail.name, thumbnail_category)

                # If the upload is successful, update the thumbnail_url field
                if thumbnail_url:
                    obj.thumbnail_url = thumbnail_url
                    print(f"Thumbnail uploaded successfully: {thumbnail_url}")
                else:
                    print("Thumbnail upload to Supabase failed.")

            except Exception as e:
                print(f"An error occurred while uploading the thumbnail: {e}")

        # Call the parent class's save_model method to save the instance
        super().save_model(request, obj, form, change)


# Admin class for ChildAchievement
class ChildAchievementAdmin(admin.ModelAdmin):
    list_display = ('child', 'achievement', 'complete')  # Display these fields
    list_filter = ('complete',)  # Filter options for completion status
    search_fields = ('child__name', 'achievement__title')  # Allow searching by child's name and achievement title


admin.site.register(Achievement, AchievementAdmin)
admin.site.register(ChildAchievement, ChildAchievementAdmin)
