
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .forms import ParentRegistrationForm
from .forms import LoginForm
from .forms import ChildAccountForm
from .models import Child,Parent
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from component.game.models import Game, GamePurchase  # Import Game and GamePurchase models
from component.quiz.models import ChildQuiz  # Import the ChildQuiz model to get quiz scores
from component.eduMaterial.models import EducationalMaterial  # For tracking time spent on materials
from component.game.models import ChildGame
from django.db import models


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
    if request.method == 'POST':
        form = ChildAccountForm(request.POST, request.FILES)
        if form.is_valid():
            child = form.save(commit=False)
            child.parent = request.user  # Associate the child with the logged-in parent
            child.save()  # UUID for childID will be generated automatically
            return redirect('choose_profile')  # Redirect to choose profile or parent dashboard
    else:
        form = ChildAccountForm()

    return render(request, 'addChild.html', {'form': form})

@login_required
def choose_profile_view(request):
    # Get all children associated with the logged-in parent
    children = Child.objects.filter(parent=request.user)
    return render(request, 'childAccount.html', {'children': children})


def child_home(request, childID):
    child = get_object_or_404(Child, childID=childID)
    return render(request, 'childHome.html', {'child': child})


@login_required
def parent_dashboard(request):
    """
    View to render the parent dashboard with child profiles, available games, and purchased games.
    """
    # Fetch the parent using the logged-in user's email
    parent = get_object_or_404(Parent, email=request.user.email)

    # Get all children associated with this parent
    children = Child.objects.filter(parent=parent)

    # Select the first child as the default selected child if children exist
    selected_child = children.first() if children.exists() else None

    # Get the IDs of purchased games by this parent
    purchased_game_ids = GamePurchase.objects.filter(parent=parent).values_list('game__gameID', flat=True)

    # Get available games that are free or already purchased by the parent
    available_games = Game.objects.filter(status=True, free=True).union(
        Game.objects.filter(status=True, gameID__in=purchased_game_ids)
    )

    # Get purchased games that are not free and not purchased by the parent
    purchased_games = Game.objects.filter(free=False).exclude(gameID__in=purchased_game_ids)

    # Pass the children and game data to the context
    context = {
        'parent': parent,
        'children': children,
        'selected_child': selected_child,  # Use this as the default child if needed
        'available_games': available_games,
        'purchased_games': purchased_games,  # Games not free and not purchased
    }

    return render(request, 'parentDashboard.html', context)



def child_detail(request, child_id):
    """
    View to display the child details, time spent on activities, and quiz scores.
    """
    # Fetch the child object using the child_id
    child = get_object_or_404(Child, childID=child_id)

    # Fetch quiz scores for the child
    quiz_scores = ChildQuiz.objects.filter(child=child).values('quiz__title', 'score')

    # Fetch time spent on different activities (Books, Videos, Quizzes, Games)
    book_time = EducationalMaterial.objects.filter(type='book', child_materials__child=child).aggregate(total_time=models.Sum('child_materials__timeSpent'))['total_time'] or 0
    video_time = EducationalMaterial.objects.filter(type='video', child_materials__child=child).aggregate(total_time=models.Sum('child_materials__timeSpent'))['total_time'] or 0
    quiz_time = ChildQuiz.objects.filter(child=child).aggregate(total_time=models.Sum('timeSpent'))['total_time'] or 0
    game_time = ChildGame.objects.filter(child=child).aggregate(total_time=models.Sum('timeSpent'))['total_time'] or 0

    # Calculate total time spent (in seconds)
    total_time_spent = sum([book_time, video_time, quiz_time, game_time])

    # Prepare context data to pass to the template
    context = {
        'child': child,
        'quiz_scores': quiz_scores,
        'book_time': book_time,  # Total time spent on books
        'video_time': video_time,  # Total time spent on videos
        'quiz_time': quiz_time,  # Total time spent on quizzes
        'game_time': game_time,  # Total time spent on games
        'total_time_spent': total_time_spent,  # Sum of all time spent
    }

    # Render the child detail template with the context data
    return render(request, 'childDetail.html', context)