from django.db import models
from django.conf import settings

from question.models import Question
from advisor.models import AdvisorProfile


class Review(models.Model):

    question = models.OneToOneField(
        Question,
        on_delete=models.CASCADE,
        related_name="review",
    )

    advisor = models.ForeignKey(
        AdvisorProfile,
        on_delete=models.CASCADE,
        related_name="reviews",
    )

    questioner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_given",
    )

    rating = models.PositiveSmallIntegerField()

    comment = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"{self.advisor.user.username} "
            f"- {self.rating}★ "
            f"({self.question.title})"
        )