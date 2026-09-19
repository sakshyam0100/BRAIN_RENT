from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import (
    notify_question_accepted,
    notify_answer_submitted,
    notify_review_received,
    notify_new_question
)


@receiver(post_save, sender='question.QuestionAssignment')
def question_assignment_created(sender, instance, created, **kwargs):
    """
    Create notification when a question is accepted by an advisor
    """
    if created:
        notify_question_accepted(instance.question, instance.advisor)


@receiver(post_save, sender='question.Answer')
def answer_submitted(sender, instance, created, **kwargs):
    """
    Create notification when an advisor submits an answer
    """
    if created:
        notify_answer_submitted(instance.question, instance.advisor)


@receiver(post_save, sender='review.Review')
def review_submitted(sender, instance, created, **kwargs):
    """
    Create notification when a questioner submits a review
    """
    if created:
        notify_review_received(instance)


@receiver(post_save, sender='question.Question')
def question_created(sender, instance, created, **kwargs):
    """
    Create notification for approved advisors when a new question is created
    """
    if created:
        notify_new_question(instance)