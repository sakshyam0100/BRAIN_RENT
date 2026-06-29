from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    icon = models.ImageField(
        upload_to="category_icons/",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name


class Question(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    questioner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class QuestionAssignment(models.Model):
    STATUS_CHOICES = [
        ("invited", "Invited"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
        ("selected", "Selected"),
        ("completed", "Completed"),
    ]

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="assignments"
    )

    advisor = models.ForeignKey(
    "advisor.AdvisorProfile",
    on_delete=models.CASCADE,
    related_name="assignments"
 )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="invited"
    )

    assigned_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ("question", "advisor")

    def __str__(self):
        return f"{self.question.title} -> {self.advisor.user.username}"