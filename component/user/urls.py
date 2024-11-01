# user/urls.py

from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('signin/', views.signin_view, name='signin'),
    path('childAccount/', views.choose_profile_view, name='choose_profile'),
    path('addChild/', views.add_child_account, name='add_child_account'),
    path('child/<uuid:childID>/', views.child_home, name='child_home'),
    path('dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('childDetail/<uuid:child_id>/', views.child_detail, name='child_detail'),
    path('subscription-plans/', views.subscription_plans_view, name='subscription_plans'),
    path('logout/', views.logout_view, name='logout'),
    path('payment/', include(('component.payment.urls', 'payment'), namespace='payment')),  # Include the payment URLs here with namespace
]
