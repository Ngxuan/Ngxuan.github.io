
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .forms import ParentRegistrationForm
from .forms import LoginForm
from .forms import ChildAccountForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from component.game.models import Game # Import Game and GamePurchase models
from component.quiz.models import ChildQuiz  # Import the ChildQuiz model to get quiz scores
from component.eduMaterial.models import EducationalMaterial  # For tracking time spent on materials
from component.game.models import ChildGame
from django.db import models
from datetime import timedelta
from component.user.models import Parent, Child, Subscription, SubscriptionPlan
from django.contrib.auth import logout
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView



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


@login_required  # Ensure the parent is logged in
def add_child_account(request):
    # Get the logged-in parent
    parent = request.user

    # Check the number of children associated with the parent
    existing_children_count = Child.objects.filter(parent=parent).count()
    # Check if there is an active subscription for the parent
    active_subscription = Subscription.objects.filter(parent=parent, subscription_end__gt=timezone.now()).first()

    # If the parent already has 3 children and no active subscription, redirect to subscription plans
    if existing_children_count >= 3:
        if active_subscription:
            # If there is an active subscription, proceed with the form submission
            form = ChildAccountForm(request.POST, request.FILES)
            if form.is_valid():
                child = form.save(commit=False)
                child.parent = parent  # Associate the child with the logged-in parent
                child.save()  # UUID for childID will be generated automatically
                return redirect('parent_dashboard')  # Redirect to choose profile or parent dashboard
        else:
            # Redirect to subscription plans if no active subscription is found
            return redirect('subscription_plans')

    # If the number of children is below the limit, proceed with the form display and submission
    if request.method == 'POST':
        form = ChildAccountForm(request.POST, request.FILES)
        if form.is_valid():
            child = form.save(commit=False)
            child.parent = parent  # Associate the child with the logged-in parent
            child.save()  # UUID for childID will be generated automatically
            return redirect('parent_dashboard')  # Redirect to choose profile or parent dashboard
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




def convert_to_seconds(value):
    """Convert a value to seconds if it's a timedelta, otherwise return the value itself."""
    if isinstance(value, models.DurationField().default):
        return value.total_seconds()
    return value



def convert_to_seconds(time_value):
    """
    Converts a timedelta object to seconds, or returns the original value if it is not a timedelta.
    """
    if isinstance(time_value, timedelta):
        return time_value.total_seconds()
    return time_value


def child_detail(request, child_id):
    """
    View to display the child details, time spent on activities, and quiz scores.
    """
    # Fetch the child object using the child_id
    child = get_object_or_404(Child, childID=child_id)

    # Fetch quiz scores for the child
    quiz_scores = ChildQuiz.objects.filter(child=child).values('quiz__title', 'score')

    # Fetch time spent on different activities (Books, Videos, Quizzes, Games)
    book_time = EducationalMaterial.objects.filter(
        type='book',
        child_edu_materials__child=child
    ).aggregate(total_time=models.Sum('child_edu_materials__timeSpent'))['total_time'] or 0

    video_time = EducationalMaterial.objects.filter(
        type='video',
        child_edu_materials__child=child
    ).aggregate(total_time=models.Sum('child_edu_materials__timeSpent'))['total_time'] or 0

    quiz_time = ChildQuiz.objects.filter(child=child).aggregate(total_time=models.Sum('timeSpent'))['total_time'] or 0
    game_time = ChildGame.objects.filter(child=child).aggregate(total_time=models.Sum('timeSpent'))['total_time'] or 0

    # Convert any datetime.timedelta objects to seconds before performing the sum
    book_time = convert_to_seconds(book_time)
    video_time = convert_to_seconds(video_time)
    quiz_time = convert_to_seconds(quiz_time)
    game_time = convert_to_seconds(game_time)

    # Ensure all values are integers or floats (seconds)
    book_time = book_time if isinstance(book_time, (int, float)) else 0
    video_time = video_time if isinstance(video_time, (int, float)) else 0
    quiz_time = quiz_time if isinstance(quiz_time, (int, float)) else 0
    game_time = game_time if isinstance(game_time, (int, float)) else 0

    # Calculate total time spent (all in seconds)
    total_time_spent = book_time + video_time + quiz_time + game_time

    # Convert total time to a readable format (e.g., minutes)
    total_time_spent_minutes = total_time_spent / 60  # Convert seconds to minutes

    # Prepare context data to pass to the template
    context = {
        'child': child,
        'quiz_scores': quiz_scores,
        'book_time': book_time / 60,  # Convert seconds to minutes
        'video_time': video_time / 60,  # Convert seconds to minutes
        'quiz_time': quiz_time / 60,  # Convert seconds to minutes
        'game_time': game_time / 60,  # Convert seconds to minutes
        'total_time_spent': total_time_spent_minutes,  # Total time spent in minutes
    }

    # Render the child detail template with the context data
    return render(request, 'childDetail.html', context)


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