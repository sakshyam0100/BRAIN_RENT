from django.db import models
from django.conf import settings


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('question_accepted', 'Question Accepted'),
        ('answer_submitted', 'Answer Submitted'),
        ('review_received', 'Review Received'),
        ('new_question', 'New Question'),
        ('payment_received', 'Payment Received'),
        ('system', 'System Notification'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        default='system'
    )

    title = models.CharField(max_length=200)
    message = models.TextField()

    related_question_id = models.IntegerField(
        null=True,
        blank=True,
        help_text='ID of related question if applicable'
    )

    related_advisor_id = models.IntegerField(
        null=True,
        blank=True,
        help_text='ID of related advisor if applicable'
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"

    def mark_as_read(self):
        self.is_read = True
        self.save()
