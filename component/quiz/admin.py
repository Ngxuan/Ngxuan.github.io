from django import forms
from django.contrib import admin
from .models import QuizQuestion, QuizQuestionOption, Quiz, ChildQuiz,QuizType
from component.supabase_client import upload_file_to_supabase  # Import the Supabase upload function

# Define a constant for the Supabase bucket name
BUCKET_NAME = 'fyp'  # Name of the bucket in Supabase storage

# Inline form for adding options to QuizQuestion
class QuizQuestionOptionInline(admin.TabularInline):
    model = QuizQuestionOption
    extra = 1  # Number of empty option fields to display by default
    fields = ('text', 'is_correct')  # Fields to display


class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('quizQuestionID', 'question')  # Display these fields in the admin list view
    search_fields = ('question',)  # Allow searching by question text
    inlines = [QuizQuestionOptionInline]  # Use the inline to add options


class QuizAdminForm(forms.ModelForm):
    upload_logo = forms.FileField(required=False, label='Upload Quiz Logo to Supabase')

    class Meta:
        model = Quiz
        fields = '__all__'
        exclude = ('quizID',)

    def save(self, commit=True):
        instance = super(QuizAdminForm, self).save(commit=False)
        upload_logo = self.cleaned_data.get('upload_logo')

        if upload_logo:
            try:
                file_content = upload_logo.read()  # Read the file content as bytes
                file_name = f"quiz_logo_{instance.quizID}.png"  # Generate a unique filename for each quiz logo
                category = 'quiz'
                public_url = upload_file_to_supabase(BUCKET_NAME, file_content, file_name, category)
                if public_url:
                    instance.thumbnail_url = public_url  # Update the thumbnail_url with the returned URL
                    print(f"Logo uploaded successfully: {public_url}")
                else:
                    print("Logo upload to Supabase failed.")
            except Exception as e:
                print(f"An error occurred while uploading the logo: {e}")

        if commit:
            instance.save()
        return instance



# Customizing the display for Quiz with the custom form
class QuizAdmin(admin.ModelAdmin):
    form = QuizAdminForm  # Use the custom form for Quiz
    list_display = ('quizID', 'title', 'thumbnail_url', 'status', 'type')  # Display quiz title, type, and other fields
    list_filter = ('status', 'type')  # Filter by status and type
    search_fields = ('quizID', 'title')  # Allow searching by quiz ID or title
    fields = ('title', 'status', 'type', 'questions', 'upload_logo')  # Include type and other fields for display
    readonly_fields = ('thumbnail_url',)  # Make thumbnail_url readonly since it's populated via upload
    exclude = ('quizID',)  # Exclude quizID from the form since it's non-editable


# Admin class for managing QuizType
class QuizTypeAdmin(admin.ModelAdmin):
    list_display = ('typeID', 'type_name')  # Display ID and type name
    search_fields = ('type_name',)  # Allow searching by type na


class ChildQuizAdmin(admin.ModelAdmin):
    list_display = ('childQuizID', 'child', 'quiz', 'status', 'score', 'timeSpent')  # Display these fields
    list_filter = ('status', 'child')  # Filter by status and child
    search_fields = ('child__name', 'quiz__title')  # Search by child name or quiz title


# Register each model with their corresponding custom admin classes
admin.site.register(QuizQuestion, QuizQuestionAdmin)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(QuizType, QuizTypeAdmin)  # Register QuizType with its admin class
admin.site.register(ChildQuiz, ChildQuizAdmin)