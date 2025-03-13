from django.db import models
from apps.multilevel.models import  Test
from apps.users.models import  User
from django.utils import timezone


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')])
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    payment_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"
    
    def __str__(self):
        return self.user.get_full_name() + " - " + self.test.title

    def save(self, *args, **kwargs):
        if self.status == 'completed':
            self.expiry_date = timezone.now()
        super().save(*args, **kwargs)
    
    
