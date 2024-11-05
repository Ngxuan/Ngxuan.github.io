# admin.py

from django import forms
from django.contrib import admin
from .models import Achievement, ChildAchievement
from component.supabase_client import upload_file_to_supabase
from component.quiz.models import QuizType  # Importing QuizType from the correct module

# Create a custom form for the Achievement model
class AchievementAdminForm(forms.ModelForm):
    upload_thumbnail = forms.FileField(required=False, label='Upload Thumbnail to Supabase')
    quiz_type = forms.ModelChoiceField(queryset=QuizType.objects.all(), required=False, label='Quiz Type')

    class Meta:
        model = Achievement
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(AchievementAdminForm, self).__init__(*args, **kwargs)

        # Check if the instance is already created (i.e., editing an existing achievement)
        if self.instance and self.instance.pk:
            # If the type is 'quiz', make quiz_type required and visible
            if self.instance.type == 'quiz':
                self.fields['quiz_type'].required = True  # Make quiz_type required
            else:
                self.fields['quiz_type'].required = False  # Otherwise, not required
                self.fields['quiz_type'].widget = forms.HiddenInput()  # Hide the field if not a quiz type
        else:
            # If creating a new instance, check if type is provided in POST data
            if 'type' in self.data and self.data['type'] == 'quiz':
                self.fields['quiz_type'].required = True  # Make quiz_type required for new quizzes
            else:
                self.fields['quiz_type'].widget = forms.HiddenInput()  # Hide the field initially

# Create the Achievement admin class with support for Supabase uploads
class AchievementAdmin(admin.ModelAdmin):
    form = AchievementAdminForm
    list_display = ('title', 'description', 'criteria', 'status', 'thumbnail_url', 'type', 'completion_metric')
    list_filter = ('status', 'type', 'completion_metric')  # Add filters for type and completion_metric
    search_fields = ('title', 'description')
    fields = ('title', 'description', 'criteria', 'status', 'thumbnail_url', 'upload_thumbnail', 'type', 'quiz_type', 'completion_metric')  # Include quiz_type in fields
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
    list_display = ('child', 'achievement', 'completionPercentage', 'complete')  # Display these fields
    list_filter = ('complete',)  # Filter options for completion status
    search_fields = ('child__name', 'achievement__title')  # Allow searching by child's name and achievement title


admin.site.register(Achievement, AchievementAdmin)
admin.site.register(ChildAchievement, ChildAchievementAdmin)
