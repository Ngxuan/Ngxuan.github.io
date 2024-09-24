

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

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
    is_staff = models.BooleanField(default=False)  # Required for admin access
    is_superuser = models.BooleanField(default=False)  # Required for superuser status
    is_active = models.BooleanField(default=True)  # Required for active status
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phoneNo']

    objects = ParentManager()


    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


# Child model
class Child(models.Model):
    childID = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    image = models.ImageField(upload_to='child_images/', blank=True, null=True)  # Optional image
    name = models.CharField(max_length=255)
    age = models.IntegerField()
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='children')  # One-to-many relationship with Parent

    def __str__(self):
        return self.name  # Display name as the string representation of Child

