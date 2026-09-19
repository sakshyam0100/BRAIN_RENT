from django.db import models
from django.conf import settings



class AdvisorProfile(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("under_review", "Under Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("suspended", "Suspended"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    bio = models.TextField()

    expertise = models.ManyToManyField(
    "question.Category",
    related_name="advisors"
 )

    experience = models.PositiveIntegerField(
        help_text="Years of experience"
    )

    consultation_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Consultation rate per session in NPR"
    )

    verification_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    def __str__(self):
        return self.user.username

class AdvisorVerification(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("under_review", "Under Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    advisor = models.OneToOneField(
        AdvisorProfile,
        on_delete=models.CASCADE,
        related_name="verification"
    )

    government_id = models.ImageField(
        upload_to="advisor_verification/government_ids/"
    )

    certificate = models.FileField(
        upload_to="advisor_verification/certificates/"
    )

    professional_license = models.FileField(
        upload_to="advisor_verification/licenses/",
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    admin_note = models.TextField(
        blank=True
    )

    verified_at = models.DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.advisor.user.username} - {self.status}"