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
    path('parentDetail/', views.parent_detail, name='parentDetail'),
    path('change-password/', views.change_password, name='change_password'),
    path('childDetail/<uuid:child_id>/', views.child_detail, name='child_detail'),
    path('subscription-plans/', views.subscription_plans_view, name='subscription_plans'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('payment/', include(('component.payment.urls', 'payment'), namespace='payment')),
    # urls.py
    path('update_child/<uuid:child_id>/', views.update_child_profile, name='update_child_profile'),
path('parent_dashboard_auth/', views.parent_dashboard_auth, name='parent_dashboard_auth'),

    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    # Use the custom password reset confirm view
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_confirm.html'),
         name='password_reset_complete'),
]
