# In your views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from paypal.standard.forms import PayPalPaymentsForm
from component.user.models import Parent, Subscription, SubscriptionPlan
from component.payment.models import Payment
import uuid
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

def create_subscription_payment(request, plan_id):
    parent = request.user  # The authenticated Parent instance
    host = request.get_host()

    # Fetch all subscription plans for the left panel
    plans = SubscriptionPlan.objects.all().order_by('price')

    # Fetch the selected subscription plan for the right panel
    selected_plan = get_object_or_404(SubscriptionPlan, id=plan_id)

    # Define PayPal payment details for the selected plan
    payment_data = {
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        'amount': str(selected_plan.price),
        'item_name': f'Subscription - {selected_plan.plan_name}',
        'invoice': str(uuid.uuid4()),
        'currency_code': 'MYR',
        'notify_url': f'http://{host}{reverse("payment:paypal-ipn")}',
        'return_url': f'http://{host}{reverse("payment:subscription_successful", kwargs={"plan_id": selected_plan.id})}',
        'cancel_url': f'http://{host}{reverse("payment:subscription_failed", kwargs={"plan_id": selected_plan.id})}',
    }

    # Create the PayPal form
    paypal_payment_form = PayPalPaymentsForm(initial=payment_data)

    # Pass the plans and selected plan to the template
    context = {
        'plans': plans,  # All available plans for the left panel
        'selected_plan': selected_plan,  # Selected plan details for the right panel
        'paypal_redirect_url': paypal_payment_form,  # PayPal form for payment
    }

    return render(request, 'checkout.html', context)

def subscription_successful(request, plan_id):
    """
    View to handle successful subscription payment and create/update the subscription.
    """
    transaction_id = request.GET.get('transaction_id')  # Capture transaction ID if available
    parent = request.user  # Get parent from the authenticated user

    # Fetch the subscription plan
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    print(f"DEBUG: Fetched SubscriptionPlan ID: {plan.id}")  # Debugging line

    # Calculate the subscription duration based on the plan
    duration_mapping = {
        'one_month': timedelta(days=30),
        'six_months': timedelta(days=182),
        'twelve_months': timedelta(days=365),
    }
    duration = duration_mapping.get(plan.plan_name, timedelta(days=30))  # Default to 30 days if not found

    # Create a Payment entry for the subscription
    payment = Payment.objects.create(
        parent=parent,
        amount=plan.price,
        transaction_id=transaction_id,
        payment_date=timezone.now()
    )

    # Update or create the Subscription
    subscription, created = Subscription.objects.get_or_create(parent=parent)
    subscription.subscription_plan = plan
    subscription.subscription_start = timezone.now()
    subscription.subscription_end = subscription.subscription_start + duration
    subscription.save()

    return render(request, 'payment-success.html', {'plan': plan})


def subscription_failed(request):
    """
    View to handle subscription payment failures.
    """
    return render(request, 'subscription-failed.html')
