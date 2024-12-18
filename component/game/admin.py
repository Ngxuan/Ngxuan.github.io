from django import forms
from django.contrib import admin
from .models import GameType, Game, GameQuestion, GameQuestionOption, ChildGame
from component.supabase_client import upload_file_to_supabase  # Import the Supabase upload function
import os
from django.conf import settings
# Define a constant for the Supabase bucket name
BUCKET_NAME = 'fyp'  # Name of the bucket in Supabase storage


# Custom form for GameQuestionOption to include image upload functionality
class GameQuestionOptionForm(forms.ModelForm):
    # File field for uploading an image to Supabase
    upload_image = forms.FileField(required=False, label='Upload Image to Supabase')

    class Meta:
        model = GameQuestionOption
        fields = '__all__'  # Include all fields in the form

    def save(self, commit=True):
        """
        Override the save method to handle image upload to Supabase storage.
        """
        instance = super(GameQuestionOptionForm, self).save(commit=False)
        upload_image = self.cleaned_data.get('upload_image')

        if upload_image:
            try:
                # Read the content of the uploaded file
                file_content = upload_image.read()
                # Generate a unique filename for the uploaded image using option ID
                file_name = f"game_option_{instance.optionID}.png"

                # Define the category/folder for game option images (stored in 'fyp/game_option' bucket)
                category = 'game_option'

                # Upload the file to Supabase storage and get the public URL
                public_url = upload_file_to_supabase(BUCKET_NAME, file_content, file_name, category)

                # If the upload is successful, update the image_url field
                if public_url:
                    instance.image_url = public_url
                    print(f"Image uploaded successfully: {public_url}")
                else:
                    print("Image upload to Supabase failed.")
            except Exception as e:
                print(f"An error occurred while uploading the image: {e}")

        if commit:
            instance.save()
        return instance


# Inline form for GameQuestionOption to use the custom form with image upload
class GameQuestionOptionInline(admin.TabularInline):
    model = GameQuestionOption
    form = GameQuestionOptionForm  # Use the custom form with image upload
    extra = 1  # Show one extra field by default
    fields = ('text', 'upload_image', 'image_url', 'is_correct')  # Display these fields, including the new upload_image


# Admin class for managing GameQuestion separately (if needed)
class GameQuestionAdmin(admin.ModelAdmin):
    list_display = ('gameQuestionID', 'question')  # Display these fields
    search_fields = ('question',)  # Enable search by question text
    inlines = [GameQuestionOptionInline]  # Include inline for options



class GameAdminForm(forms.ModelForm):
    # Create custom file fields for uploading the game logo and HTML file
    upload_logo = forms.FileField(required=False, label='Upload Game Logo to Supabase')
    upload_html = forms.FileField(required=False, label='Upload HTML Template File')

    class Meta:
        model = Game
        fields = '__all__'
        exclude = ('gameID',)  # Exclude gameID since it’s non-editable

    def save(self, commit=True):
        """
        Override the save method to handle logo upload to Supabase and HTML template file storage.
        """
        instance = super(GameAdminForm, self).save(commit=False)
        upload_logo = self.cleaned_data.get('upload_logo')
        upload_html = self.cleaned_data.get('upload_html')

        # Handle logo upload to Supabase
        if upload_logo:
            try:
                # Read the content of the uploaded file
                file_content = upload_logo.read()
                file_name = f"game_logo_{instance.gameID}.png"  # Generate a unique filename for each game logo

                # Define the category/folder for game logos (stored in 'fyp/game' bucket)
                category = 'game'

                # Upload the file to Supabase storage and get the public URL
                public_url = upload_file_to_supabase(BUCKET_NAME, file_content, file_name, category)

                # If the upload is successful, update the thumbnail_url field
                if public_url:
                    instance.thumbnail_url = public_url
                    print(f"Logo uploaded successfully: {public_url}")
                else:
                    print("Logo upload to Supabase failed.")
            except Exception as e:
                print(f"An error occurred while uploading the logo: {e}")

        # Handle HTML file upload to the templates directory
        if upload_html:
            try:
                self.save_html_file(upload_html, instance)  # Save the uploaded HTML file
            except Exception as e:
                print(f"An error occurred while saving the HTML file: {e}")

        if commit:
            instance.save()
        return instance

    def save_html_file(self, upload_html, instance):
        """
        Save the uploaded HTML file to the templates directory.
        """
        # Ensure the templates/games directory exists
        templates_path = os.path.join(settings.BASE_DIR, 'templates/games')
        os.makedirs(templates_path, exist_ok=True)

        # File name for the HTML file
        file_name = f"game_{instance.gameID}.html"
        file_path = os.path.join(templates_path, file_name)

        # Save the uploaded file content to the desired location
        with open(file_path, 'wb') as f:
            for chunk in upload_html.chunks():
                f.write(chunk)

        # Save the template name in the model instance
        instance.template_name = f"games/{file_name}"
        print(f"HTML file uploaded successfully to: {file_path}")

# Admin class for managing GameType
class GameTypeAdmin(admin.ModelAdmin):
    list_display = ('typeID', 'type_name')  # Display type ID and type name
    search_fields = ('type_name',)  # Enable search by type name


# Admin class for managing Game with related questions
class GameAdmin(admin.ModelAdmin):
    form = GameAdminForm  # Use the custom form for Game
    list_display = ('gameID', 'title', 'type', 'thumbnail_url', 'status', 'free', 'template_name')  # Display template name
    list_filter = ('status', 'free', 'type')  # Enable filtering by status, free, and type
    search_fields = ('title', 'type__type_name')  # Enable search by title or type name
    fields = ('title', 'type', 'description', 'status', 'questions', 'free', 'upload_logo', 'upload_html')  # Fields to include in the form
    readonly_fields = ('thumbnail_url', 'template_name')  # Make some fields readonly

# Admin class for managing ChildGame records (optional)
class ChildGameAdmin(admin.ModelAdmin):
    list_display = ('childGameID', 'child', 'game', 'timeSpent')  # Display these fields
    list_filter = ('child', 'game')  # Enable filtering by child and game
    search_fields = ('child__name', 'game__title')  # Enable search by child name or game title


# Register models with their corresponding admin classes
admin.site.register(GameType, GameTypeAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(GameQuestion, GameQuestionAdmin)

