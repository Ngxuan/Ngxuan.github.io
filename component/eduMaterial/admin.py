# admin.py

from django import forms
from django.contrib import admin
from .models import EducationalMaterial, ChildEduMaterial
from component.supabase_client import upload_file_to_supabase  # Import your Supabase upload function

class EducationalMaterialAdminForm(forms.ModelForm):
    # Create custom file fields for uploading files and thumbnails directly to Supabase
    upload_file = forms.FileField(required=False, label='Upload File to Supabase')
    upload_thumbnail = forms.FileField(required=False, label='Upload Thumbnail to Supabase')

    class Meta:
        model = EducationalMaterial
        fields = '__all__'  # Include all fields from the model

class EducationalMaterialAdmin(admin.ModelAdmin):
    form = EducationalMaterialAdminForm
    list_display = ('title', 'type', 'description', 'file_url', 'thumbnail_url')
    list_filter = ('type',)
    search_fields = ('title',)
    fields = ('title', 'description', 'type', 'file_url', 'thumbnail_url', 'upload_file', 'upload_thumbnail')  # Include thumbnail field
    readonly_fields = ('file_url', 'thumbnail_url')  # Make file_url and thumbnail_url readonly

    def save_model(self, request, obj, form, change):
        """
        Override save_model to handle file and thumbnail uploads to Supabase storage.
        """
        uploaded_file = form.cleaned_data.get('upload_file')
        uploaded_thumbnail = form.cleaned_data.get('upload_thumbnail')

        # Define the bucket name for main files and thumbnails
        bucket_name = 'fyp'  # Main bucket name for files and thumbnails

        # Handle main file upload
        if uploaded_file:
            try:
                # Read the content of the uploaded file
                file_content = uploaded_file.read()  # Read the file content as bytes

                # Determine the category based on the type of the educational material
                category = obj.type  # This should be either 'book', 'video', etc.

                # Log the file information for debugging
                print(f"Uploading file: {uploaded_file.name}, Content length: {len(file_content)} bytes, Category: {category}")

                # Upload the file to Supabase storage and get the public URL
                public_url = upload_file_to_supabase(bucket_name, file_content, uploaded_file.name, category)

                # If the upload is successful, update the file_url field
                if public_url:
                    obj.file_url = public_url
                    print(f"File uploaded successfully: {public_url}")
                else:
                    print("File upload to Supabase failed.")

            except Exception as e:
                print(f"An error occurred while uploading the file: {e}")

        # Handle thumbnail upload
        if uploaded_thumbnail:
            try:
                # Read the content of the uploaded thumbnail
                thumbnail_content = uploaded_thumbnail.read()  # Read the thumbnail content as bytes

                # Create a separate category/folder for thumbnails, e.g., 'video_thumbnails', 'book_thumbnails'
                thumbnail_category = f"{category}_thumbnails"  # e.g., 'video_thumbnails' or 'book_thumbnails'

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
admin.site.register(EducationalMaterial, EducationalMaterialAdmin)
admin.site.register(ChildEduMaterial)
