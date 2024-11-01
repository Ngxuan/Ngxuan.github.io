# admin.py

from django import forms
from django.contrib import admin
from .models import Achievement, ChildAchievement
from component.supabase_client import upload_file_to_supabase  #  # Import your Supabase upload function

# Create a custom form for the Achievement model
class AchievementAdminForm(forms.ModelForm):
    # Create custom file fields for uploading thumbnails directly to Supabase
    upload_thumbnail = forms.FileField(required=False, label='Upload Thumbnail to Supabase')

    class Meta:
        model = Achievement
        fields = '__all__'  # Include all fields from the model

# Create the Achievement admin class with support for Supabase uploads
class AchievementAdmin(admin.ModelAdmin):
    form = AchievementAdminForm
    list_display = ('title', 'description', 'criteria', 'status', 'thumbnail_url')
    list_filter = ('status',)
    search_fields = ('title', 'description')
    fields = ('title', 'description', 'criteria', 'rewards', 'status', 'thumbnail_url', 'upload_thumbnail')
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

                # Use 'achievements_thumbnails' as the category for thumbnails
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





# Register the admin models
admin.site.register(Achievement, AchievementAdmin)
