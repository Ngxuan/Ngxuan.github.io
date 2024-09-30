# admin.py

from django import forms
from django.contrib import admin
from .models import EducationalMaterial, ChildEduMaterial
from component.supabase_client import upload_file_to_supabase  # Import your Supabase upload function

class EducationalMaterialAdminForm(forms.ModelForm):
    # Create a custom file field for uploading files directly to Supabase
    upload_file = forms.FileField(required=False, label='Upload File to Supabase')

    class Meta:
        model = EducationalMaterial
        fields = '__all__'  # Include all fields from the model

class EducationalMaterialAdmin(admin.ModelAdmin):
    form = EducationalMaterialAdminForm
    list_display = ('title', 'type', 'description', 'file_url')  # Show file_url in the list view
    list_filter = ('type',)
    search_fields = ('title',)
    fields = ('title', 'description', 'type', 'file_url', 'upload_file')  # Include file upload field in admin
    readonly_fields = ('file_url',)  # Make file_url readonly so it's not editable

    def save_model(self, request, obj, form, change):
        """
        Override save_model to handle file uploads to Supabase storage.
        """
        # Get the uploaded file from the custom form field
        uploaded_file = form.cleaned_data.get('upload_file')

        if uploaded_file:
            try:
                # Read the content of the uploaded file
                file_content = uploaded_file.read()  # Read the file content as bytes

                # Define the bucket name and file path in Supabase
                bucket_name = 'fyp'  # Supabase bucket name
                file_name = uploaded_file.name  # File name without the path

                # Log the file information for debugging
                print(f"Uploading file: {file_name}, Content length: {len(file_content)} bytes")

                # Upload the file to Supabase storage and get the public URL
                public_url = upload_file_to_supabase(bucket_name, file_content, file_name)

                # If the upload is successful, update the file_url field
                if public_url:
                    obj.file_url = public_url
                    print(f"File uploaded successfully: {public_url}")
                else:
                    print("File upload to Supabase failed.")

            except Exception as e:
                print(f"An error occurred while uploading the file: {e}")

        # Call the parent class's save_model method to save the instance
        super().save_model(request, obj, form, change)


# Register the admin models
admin.site.register(EducationalMaterial, EducationalMaterialAdmin)
admin.site.register(ChildEduMaterial)
