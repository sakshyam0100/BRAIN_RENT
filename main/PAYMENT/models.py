from django.db import models
from django.conf import settings
from question.models import Question
from advisor.models import AdvisorProfile


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    CURRENCY_CHOICES = [
        ('NPR', 'Nepali Rupee'),
    ]

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    advisor = models.ForeignKey(
        AdvisorProfile,
        on_delete=models.CASCADE,
        related_name='received_payments'
    )
    
    questioner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='made_payments'
    )
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='NPR'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Khalti specific fields
    khalti_txn_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Khalti transaction ID'
    )
    
    khalti_idx = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Khalti payment index'
    )
    
    # Payment metadata
    payment_method = models.CharField(
        max_length=50,
        default='khalti'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Payment {self.id} - {self.questioner.username} to {self.advisor.user.username} - {self.amount} {self.currency}"
    
    def mark_completed(self, txn_id=None, idx=None):
        """Mark payment as completed"""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        if txn_id:
            self.khalti_txn_id = txn_id
        if idx:
            self.khalti_idx = idx
        self.save()
    
    def mark_failed(self):
        """Mark payment as failed"""
        self.status = 'failed'
        self.save()
    
    def mark_refunded(self):
        """Mark payment as refunded"""
        from django.utils import timezone
        self.status = 'refunded'
        self.completed_at = timezone.now()
        self.save()
