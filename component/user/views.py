import uuid


import re

from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.views.decorators.http import require_POST

from .forms import ParentRegistrationForm, ParentDetailForm
from .forms import LoginForm
from .forms import ChildAccountForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from component.game.models import Game, ChildGameLog  # Import Game and GamePurchase models
from component.quiz.models import ChildQuiz, QuizType, ChildQuizLog  # Import the ChildQuiz model to get quiz scores
from component.eduMaterial.models import EducationalMaterial  # For tracking time spent on materials
from component.game.models import ChildGame
from django.db import models
from datetime import timedelta
from component.user.models import Parent, Child, Subscription, SubscriptionPlan
from django.contrib.auth import logout
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from ..supabase_client import sanitize_file_name, upload_file_to_supabase


def signup_view(request):
    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
                parent = form.save(commit=False)
                parent.set_password(form.cleaned_data['password1'])  # Hash the password
                parent.is_staff = False  # Ensure that the user is not a staff/admin
                parent.is_superuser = False  # Ensure the user is not a superuser
                parent.save()  # Save the parent instance
                login(request, parent)  # Automatically log the user in
                return redirect('choose_profile')  # Redirect to the sign-in page


    else:
        form = ParentRegistrationForm()  # Create a blank form for GET requests

    return render(request, 'signUp.html', {'form': form})



def signin_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            # Authenticate the user
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                return redirect('choose_profile')  # Change 'home' to your desired redirect URL
            else:
                messages.error(request, 'Invalid email or password.')

    else:
        form = LoginForm()

    return render(request, 'signin.html', {'form': form})

def logout_view(request):
    #logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')  # Redirect to login page or homepage

from django.core.exceptions import ValidationError, PermissionDenied
from datetime import timedelta

@login_required
def add_child_account(request):
    parent = request.user

    # Check the number of children associated with the parent
    existing_children_count = Child.objects.filter(parent=parent).count()
    active_subscription = Subscription.objects.filter(parent=parent, subscription_end__gt=timezone.now()).first()

    # If the parent already has 3 children and no active subscription, redirect to subscription plans
    if existing_children_count >= 3 and not active_subscription:
        return redirect('subscription_plans')

    if request.method == 'POST':
        form = ChildAccountForm(request.POST, request.FILES)
        if form.is_valid():
            # Extract the birthday from the form's cleaned data
            birthday = form.cleaned_data.get('birthday')

            # Validate the birthday
            if birthday:
                today = timezone.now().date()
                min_age_date = today - timedelta(days=365)  # Child must be at least 1 year old
                max_age_date = today - timedelta(days=365 * 5)  # Child cannot be older than 5 years

                if birthday > min_age_date:
                    form.add_error('birthday', 'Child must be at least 1 year old.')
                elif birthday < max_age_date:
                    form.add_error('birthday', 'Child cannot be older than 5 year old.')

            # If there are any form errors after the custom validation
            if form.errors:
                return render(request, 'addChild.html', {'form': form})

            # If the form is still valid, proceed with saving the child
            child = form.save(commit=False)
            child.parent = parent  # Associate the child with the logged-in parent

            # Handle image upload
            upload_image = form.cleaned_data.get('image')
            if upload_image and hasattr(upload_image, 'read'):
                unique_filename = f"{uuid.uuid4()}_{upload_image.name}"
                image_url = upload_file_to_supabase('fyp', upload_image.read(), unique_filename, 'profile_images')
                if image_url:
                    child.image = image_url  # Set the uploaded image URL
            else:
                child.image = None  # Set to None if no image uploaded

            child.save()
            return redirect('parent_dashboard')
    else:
        form = ChildAccountForm()

    return render(request, 'addChild.html', {'form': form})





@login_required
def choose_profile_view(request):
    # Get only active children associated with the logged-in parent
    children = Child.objects.filter(parent=request.user, is_active=True)

    # Check if there's an active subscription for the parent
    active_subscription = Subscription.objects.filter(
        parent=request.user, subscription_end__gt=timezone.now()
    ).exists()

    return render(request, 'childAccount.html', {
        'children': children,
        'active_subscription': active_subscription,
    })


def child_home(request, childID):
    child = get_object_or_404(Child, childID=childID)
    return render(request, 'childHome.html', {'child': child})


@login_required
def parent_dashboard(request):
    """
    View to render the parent dashboard with child profiles and games,
    showing only active child accounts.
    """
    # Fetch the parent using the logged-in user's email
    parent = get_object_or_404(Parent, email=request.user.email)

    # Check if the parent has an active subscription
    subscription = getattr(parent, 'subscription', None)  # Safely get the subscription if it exists
    has_active_subscription = subscription.is_active() if subscription else False

    # Get only active children associated with this parent
    children = Child.objects.filter(parent=parent, is_active=True).order_by('name')

    # Select the first active child as the default selected child if any exist
    selected_child = children.first() if children.exists() else None

    # Separate games into free and non-free categories
    available_games = Game.objects.filter(status=True, free=True)  # Free active games
    purchased_games = Game.objects.filter(status=True, free=False)  # Paid active games

    # Pass the children and separated game data to the context
    context = {
        'parent': parent,
        'children': children,
        'selected_child': selected_child,
        'available_games': available_games,
        'purchased_games': purchased_games,
        'has_active_subscription': has_active_subscription,  # Used in the template if needed
    }

    return render(request, 'parentDashboard.html', context)


@login_required
def parent_dashboard_auth(request):
    if request.method == 'POST':
        # Get the password entered in the modal form
        password = request.POST.get('parent_password')

        # Check if the entered password is correct for the logged-in user
        user = authenticate(request, username=request.user.email, password=password)
        if user is not None:
            # If the password is correct, redirect to the parent dashboard
            return redirect('parent_dashboard')
        else:
            # If the password is incorrect, show an error message
            messages.error(request, 'Incorrect password. Please try again.')
            return redirect('choose_profile')  # Redirect back to the profile selection page

    # In case of a GET request or any other method, redirect to the profile selection page
    return redirect('choose_profile')



def convert_to_seconds(value):
    """Helper function to convert timedelta or None to seconds."""
    if isinstance(value, timedelta):
        return value.total_seconds()
    return value if isinstance(value, (int, float)) else 0



def child_detail(request, child_id):
    """
    View to display the child details, time spent on activities, and quiz scores.
    Allows parents to filter by predefined ranges or custom date ranges.
    """
    # Fetch the child object using the child_id
    child = get_object_or_404(Child, childID=child_id)

    # Fetch quiz scores for the child
    quiz_scores = ChildQuiz.objects.filter(child=child).values('quiz__title', 'score', 'quiz__type__type_name')

    # Fetch all quiz types for the filter dropdown
    quiz_types = QuizType.objects.all()  # Assuming QuizType is your model for quiz types

    # Get the time filter and custom dates from the request
    time_filter = request.GET.get('time_filter', 'daily')
    custom_start_date_str = request.GET.get('custom_start_date')
    custom_end_date_str = request.GET.get('custom_end_date')

    # Initialize start_date and end_date
    start_date = None
    end_date = None

    # Check if custom dates are provided
    if custom_start_date_str and custom_end_date_str:
        try:
            # Parse the custom dates
            start_date = datetime.strptime(custom_start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(custom_end_date_str, '%Y-%m-%d')

            # Adjust end_date to include the entire day
            end_date = end_date + timedelta(days=1) - timedelta(seconds=1)

            # Make the dates timezone-aware
            start_date = make_aware(start_date)
            end_date = make_aware(end_date)

            # Format the dates for display
            formatted_start_date = start_date.strftime('%B %d, %Y')  # Example: "November 29, 2024"
            formatted_end_date = end_date.strftime('%B %d, %Y')      # Example: "December 03, 2024"

        except ValueError:
            # If parsing fails, default to time_filter
            start_date, end_date, formatted_start_date, formatted_end_date = get_date_range(time_filter)
    else:
        # If no custom dates, use time_filter
        start_date, end_date, formatted_start_date, formatted_end_date = get_date_range(time_filter)

    print(f"Start date for filter '{time_filter}': {start_date}")

    # Fetch time spent on different activities (Books, Videos, Quizzes, Games)
    # Total time spent on books by the child within the selected date range
    book_time = EducationalMaterial.objects.filter(
        type='book',
        child_edu_material_log__child=child,  # Access the related 'child_edu_material_log' related manager
        child_edu_material_log__access_date__gte=start_date  # Filter on the 'access_date' field
    ).aggregate(total_time=Sum('child_edu_material_log__time_spent'))['total_time'] or timedelta(0)

    # Similarly for videos
    video_time = EducationalMaterial.objects.filter(
        type='video',
        child_edu_material_log__child=child,
        child_edu_material_log__access_date__gte=start_date  # Filter on the 'access_date' field
    ).aggregate(total_time=Sum('child_edu_material_log__time_spent'))['total_time'] or timedelta(0)

    # For quizzes
    quiz_time = ChildQuizLog.objects.filter(
        child=child,
        access_date__gte=start_date  # 'access_date' is directly on the 'ChildQuizLog' model
    ).aggregate(total_time=Sum('time_spent'))['total_time'] or timedelta(0)

    # For games
    game_time = ChildGameLog.objects.filter(
        child=child,
        access_date__gte=start_date  # 'access_date' is directly on the 'ChildGameLog' model
    ).aggregate(total_time=Sum('time_spent'))['total_time'] or timedelta(0)

    # Ensure all time values are converted to seconds (use convert_to_seconds utility)
    book_time_seconds = convert_to_seconds(book_time)
    video_time_seconds = convert_to_seconds(video_time)
    quiz_time_seconds = convert_to_seconds(quiz_time)
    game_time_seconds = convert_to_seconds(game_time)

    # Calculate total time spent (all in seconds)
    total_time_spent_seconds = book_time_seconds + video_time_seconds + quiz_time_seconds + game_time_seconds

    # Convert total time to minutes and then calculate hours and minutes
    total_minutes = total_time_spent_seconds // 60  # Total minutes
    hours = total_minutes // 60  # Get hours (integer division)
    remaining_minutes = total_minutes % 60  # Get remaining minutes after hours

    # Prepare context data to pass to the template
    context = {
        'child': child,
        'quiz_scores': quiz_scores,
        'quiz_types': quiz_types,  # Pass the quiz types to the template
        'book_time': book_time_seconds / 60,  # Convert seconds to minutes for display
        'video_time': video_time_seconds / 60,  # Convert seconds to minutes for display
        'quiz_time': quiz_time_seconds / 60,  # Convert seconds to minutes for display
        'game_time': game_time_seconds / 60,  # Convert seconds to minutes for display
        'total_time_spent_hours': hours,  # Pass hours to template
        'total_time_spent_minutes': remaining_minutes,  # Pass minutes to template
        'time_filter': time_filter,  # Pass the time filter to the template
        'formatted_start_date': formatted_start_date,  # Passing the formatted start date
        'formatted_end_date': formatted_end_date,
        'custom_start_date': custom_start_date_str if custom_start_date_str else '',
        'custom_end_date': custom_end_date_str if custom_end_date_str else '',
    }

    # Render the child detail template with the context data
    return render(request, 'childDetail.html', context)

def get_date_range(time_filter):
    """
    Helper function to determine the start_date and end_date based on the time_filter.
    Returns a tuple of (start_date, end_date, formatted_start_date, formatted_end_date).
    """
    now = datetime.now()
    if time_filter == 'daily':
        start_date = now - timedelta(days=1)
    elif time_filter == 'weekly':
        start_date = now - timedelta(weeks=1)
    elif time_filter == 'monthly':
        start_date = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=1)  # Default to daily

    end_date = now

    # Ensure the time is aware (timezone-aware datetime object)
    start_date = make_aware(start_date)
    end_date = make_aware(end_date)

    # Format the start date and end date for display
    formatted_start_date = start_date.strftime('%B %d, %Y')  # Example: "November 29, 2024"
    formatted_end_date = end_date.strftime('%B %d, %Y')      # Example: "December 03, 2024"

    return start_date, end_date, formatted_start_date, formatted_end_date



def subscription_plans_view(request):
    parent = request.user  # Assumes the parent is the logged-in user

    # Check if the parent has an active subscription
    active_subscription = Subscription.objects.filter(parent=parent, subscription_end__gt=timezone.now()).first()

    if active_subscription:
        # Fetch the active subscription plan details
        plan = active_subscription.subscription_plan
        context = {
            'active_subscription': active_subscription,
            'plan': plan,
        }
    else:
        # Fetch all subscription plans if there is no active subscription
        plans = SubscriptionPlan.objects.all().order_by('price')

        # Calculate monthly prices and attach them to the plan objects
        for plan in plans:
            duration_mapping = {
                '1 month': 1,
                '6 months': 6,
                '12 months': 12,
            }
            months = duration_mapping.get(plan.plan_name, 1)
            plan.monthly_price_calculated = round(plan.price / months, 2)

        context = {
            'plans': plans,
        }

    return render(request, 'subscription.html', context)



def logout_view(request):
    logout(request)
    return redirect('signin')




class ForgotPasswordView(PasswordResetView):
    template_name = 'forgotPassword.html'  # The form template
    html_email_template_name = 'password_reset_email.html'   # HTML email content template
    subject_template_name = 'passwordResetEmail.txt'  # Subject template for the email
    success_url = reverse_lazy('forgot_password')  # Redirect to the same page after submission

    def form_valid(self, form):
        # Display a success message in the template after submission
        messages.success(self.request, "An email has been sent with instructions to reset your password. Please check your inbox.")
        return super().form_valid(form)

# Custom Password Reset Confirm View
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')  # Redirect to success page

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session['password_reset_success'] = True  # Flag for success message
        return response

    def get(self, request, *args, **kwargs):
        # Clear the success flag after displaying it
        if 'password_reset_success' in request.session:
            del request.session['password_reset_success']
        return super().get(request, *args, **kwargs)


@login_required
def update_child_profile(request, child_id):
    child = get_object_or_404(Child, childID=child_id)  # Fetch the child instance
    if request.method == 'POST':
        form = ChildAccountForm(request.POST, request.FILES, instance=child)  # Ensure FILES is included
        if form.is_valid():
            # Get the uploaded image
            upload_image = form.cleaned_data.get('image')

            # Check if a new image was uploaded and that it is a valid file object
            if upload_image and hasattr(upload_image, 'read'):  # Check if it's a file-like object
                try:
                    # Read the image content as bytes
                    file_content = upload_image.read()
                    unique_filename = f"{uuid.uuid4()}_{sanitize_file_name(upload_image.name)}"
                    bucket_name = 'fyp'
                    category = 'profile_images'

                    # Attempt to upload the file to Supabase
                    image_url = upload_file_to_supabase(bucket_name, file_content, unique_filename, category)
                    if image_url:
                        child.image = image_url  # Update child's image if a new image is uploaded
                    else:
                        return JsonResponse({'success': False, 'message': 'Failed to upload image to Supabase.'},
                                             status=400)
                except Exception as e:
                    print(f"Error during upload: {e}")  # Log any upload errors
                    return JsonResponse({'success': False, 'message': 'An error occurred while uploading the image.'},
                                         status=500)

            # Save the rest of the form data without modifying the image if no new image was uploaded
            form.save()  # This saves the child's name and age regardless of whether the image is updated
            return JsonResponse({'success': True, 'message': 'Profile updated successfully!'})
        else:
            # Collect custom error messages and return them as a JSON response
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    if field == 'birthday' and 'age_under_1' in error:
                        error_messages.append("Child must be at least 1 year old.")
                    elif field == 'birthday' and 'age_over_5' in error:
                        error_messages.append("Child cannot be older than 5 year old.")
                    else:
                        error_messages.append(error)

            return JsonResponse({'success': False, 'message': 'Error(s) occurred', 'errors': error_messages}, status=400)

    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)



@login_required
def parent_detail(request):
    parent = get_object_or_404(Parent, email=request.user.email)

    if request.method == 'POST':
        form = ParentDetailForm(request.POST, request.FILES, instance=parent)

        if form.is_valid():
            # Check if a new image was uploaded
            upload_image = form.cleaned_data.get('image')
            if upload_image and hasattr(upload_image, 'read'):
                # Generate a unique filename
                unique_filename = f"{uuid.uuid4()}_{upload_image.name}"
                # Upload to Supabase and get URL
                image_url = upload_file_to_supabase('fyp', upload_image.read(), unique_filename, 'profile_images')

                if image_url:
                    parent.image = image_url  # Save image URL to database

            # Save other fields in the form except the email
            form.save()  # This saves the name, phone number, and image URL
            return redirect('parentDetail')  # Redirect or provide a success response

        else:
            print(form.errors)  # Debug form errors if any
    else:
        form = ParentDetailForm(instance=parent)

    context = {
        'form': form,
        'parent': parent,
    }
    return render(request, 'parentDetail.html', context)


@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')

        # Check if the current password is correct
        if request.user.check_password(current_password):
            # Validate the new password format
            if len(new_password) < 8:
                messages.error(request, "New password is too short. It must contain at least 8 characters.")
            elif not re.search(r"[!@#$%^&*(),.?\":{}|<>]", new_password):
                messages.error(request, "New password must contain at least one special character.")
            else:
                # If validations pass, set the new password
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keep the user logged in after password change

                # Add a success message and redirect
                messages.success(request, 'Your password was updated successfully!')
                return redirect('change_password')  # Redirect to show the success message

        else:
            # Add an error message if the current password is incorrect
            messages.error(request, 'Current password is incorrect.')

    return render(request, 'changePassword.html')


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Child  # Ensure this import is correct

@require_POST
@login_required
def delete_child_account(request):
    child_id = request.POST.get('child_id')
    print(f"Delete request received for child_id: {child_id}")

    if not child_id:
        print("Error: No child ID provided.")
        return JsonResponse({'success': False, 'error': 'No child ID provided.'}, status=400)

    try:
        child = Child.objects.get(childID=child_id)
        print(f"Child found: {child.name}")

        # **Access the Parent directly as request.user**
        if child.parent != request.user:
            print("Permission denied: User attempted to delete a child not associated with them.")
            raise PermissionDenied("You do not have permission to delete this child account.")

        child.delete()
        print(f"Child account '{child.name}' deleted successfully.")
        return JsonResponse({'success': True})

    except Child.DoesNotExist:
        print("Error: Child does not exist.")
        return JsonResponse({'success': False, 'error': 'Child does not exist.'}, status=404)

    except PermissionDenied as pd:
        print(f"Permission Denied: {pd}")
        return JsonResponse({'success': False, 'error': str(pd)}, status=403)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return JsonResponse({'success': False, 'error': 'An unexpected error occurred.'}, status=500)
