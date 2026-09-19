from .models import Notification


def create_notification(recipient, notification_type, title, message, 
                     related_question_id=None, related_advisor_id=None):
    """
    Create a notification for a user
    """
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        related_question_id=related_question_id,
        related_advisor_id=related_advisor_id
    )


def notify_question_accepted(question, advisor):
    """Notify questioner that their question was accepted"""
    return create_notification(
        recipient=question.questioner,
        notification_type='question_accepted',
        title='Your Question Has Been Accepted',
        message=f'Advisor {advisor.user.username} has accepted your question: "{question.title}"',
        related_question_id=question.id,
        related_advisor_id=advisor.id
    )


def notify_answer_submitted(question, advisor):
    """Notify questioner that an answer has been submitted"""
    return create_notification(
        recipient=question.questioner,
        notification_type='answer_submitted',
        title='Answer Submitted for Your Question',
        message=f'Advisor {advisor.user.username} has submitted an answer for your question: "{question.title}". Your question is now completed and you can leave a review.',
        related_question_id=question.id,
        related_advisor_id=advisor.id
    )


def notify_review_received(review):
    """Notify advisor that they received a review"""
    return create_notification(
        recipient=review.advisor.user,
        notification_type='review_received',
        title='New Review Received',
        message=f'You received a {review.rating}-star review for question: "{review.question.title}"',
        related_question_id=review.question.id,
        related_advisor_id=review.advisor.id
    )


def notify_new_question(question):
    """Notify approved advisors about new questions in their expertise areas"""
    from advisor.models import AdvisorProfile
    
    # Get advisors with matching expertise
    advisors = AdvisorProfile.objects.filter(
        verification_status='approved',
        expertise=question.category
    ).distinct()
    
    notifications = []
    for advisor in advisors:
        notification = create_notification(
            recipient=advisor.user,
            notification_type='new_question',
            title='New Question Available',
            message=f'A new question "{question.title}" in {question.category.name} is available for acceptance.',
            related_question_id=question.id
        )
        notifications.append(notification)
    
    return notifications