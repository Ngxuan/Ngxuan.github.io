# admin.py

from django.contrib import admin
from .models import Parent, Child

# Basic model registration
admin.site.register(Parent)
admin.site.register(Child)