

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from datetime import timedelta
from django.db import models
from django.utils import timezone

# Custom user manager for handling Parent (User) creation

class ParentManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)

class Parent(AbstractBaseUser):
    parentID = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    image = models.ImageField(upload_to='parent_images/', blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=False)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    phoneNo = models.CharField(max_length=20)
    status = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phoneNo']

    objects = ParentManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    def can_add_child(self):
        # Allow only three free accounts if there's no subscription
        return self.children.count() < 3 or (self.subscription and self.subscription.is_active())

    def has_premium_access(self):
        # Check if the parent has an active subscription for premium access
        return self.subscription and self.subscription.is_active()


class SubscriptionPlan(models.Model):
    plan_name = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.plan_name} - RM {self.price}"


class Subscription(models.Model):
    parent = models.OneToOneField(Parent, on_delete=models.CASCADE, related_name='subscription')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    subscription_start = models.DateTimeField(default=timezone.now)
    subscription_end = models.DateTimeField(null=True, blank=True)

    def activate_subscription(self, subscription_plan):
        """Activate or renew a subscription."""
        self.subscription_plan = subscription_plan
        self.subscription_start = timezone.now()
        self.subscription_end = self.calculate_subscription_end(subscription_plan)
        self.save()

    def calculate_subscription_end(self, subscription_plan):
        """Set the subscription end date based on the selected plan."""
        if subscription_plan:
            if subscription_plan.plan_name == '1 Month':
                return self.subscription_start + timedelta(days=30)
            elif subscription_plan.plan_name == '6 Months':
                return self.subscription_start + timedelta(days=182)  # Approximate 6 months
            elif subscription_plan.plan_name == '12 Months':
                return self.subscription_start + timedelta(days=365)

    def is_active(self):
        """Check if the subscription is currently active."""
        return timezone.now() < self.subscription_end if self.subscription_end else False

    def __str__(self):
        return f"{self.parent.name}'s Subscription ({self.subscription_plan})"



class Child(models.Model):
    childID = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    image = models.ImageField(upload_to='child_images/', blank=True, null=True)
    name = models.CharField(max_length=255)
    age = models.IntegerField()
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='children')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

