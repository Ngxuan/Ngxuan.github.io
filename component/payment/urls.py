
from . import views
from django.urls import path, include

urlpatterns = [
    path('create_subscription_payment/<int:plan_id>/', views.create_subscription_payment, name='create_subscription_payment'),
    path('subscription_successful/<int:plan_id>/', views.subscription_successful, name='subscription_successful'),
    path('subscription_failed/<int:plan_id>/', views.subscription_failed, name='subscription_failed'),
    path('paypal-ipn/', include('paypal.standard.ipn.urls')),
]