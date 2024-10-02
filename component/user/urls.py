from django.urls import path
from . import views


urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('signin/', views.signin_view, name='signin'),
    path('childAccount/', views.choose_profile_view, name='choose_profile'),
    path('addChild/', views.add_child_account, name='add_child_account'),
    path('child/<uuid:childID>/', views.child_home, name='child_home'),
    path('dashboard/', views.parent_dashboard, name='parent_dashboard'),
    path('childDetail/<uuid:child_id>/', views.child_detail, name='child_detail'),

]