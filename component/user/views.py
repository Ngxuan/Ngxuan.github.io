
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .forms import ParentRegistrationForm
from .forms import LoginForm
from .forms import ChildAccountForm
from .models import Child
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404


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