# admin.py

from django.contrib import admin
from .models import Parent, Child, Subscription, SubscriptionPlan

# Basic model registration
admin.site.register(Parent)
admin.site.register(Child)

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('plan_name', 'price')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('parent', 'subscription_plan', 'subscription_start', 'subscription_end', 'is_active')