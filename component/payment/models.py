from django.db import models
from django.utils import timezone
import uuid
from component.user.models import Parent



class Payment(models.Model):
    paymentID = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    payment_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Payment {self.paymentID} by {self.parent.email if self.parent else 'Anonymous'}"
