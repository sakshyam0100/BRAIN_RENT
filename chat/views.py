from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Count, Q
from django.views.decorators.http import require_POST
from django.utils import timezone
import json

from advisor.models import AdvisorProfile
from question.models import QuestionAssignment
from .models import Conversation, Message
from .forms import MessageForm


@login_required
def conversation_detail(request, question_id):

    # Try to get existing conversation or create one if the question is accepted
    from question.models import Question
    question = get_object_or_404(Question, id=question_id)

    conversation, created = Conversation.objects.get_or_create(
        question=question
    )

    user = request.user

    if user.role == "questioner":

        if conversation.question.questioner != user:
            return HttpResponseForbidden("Access Denied")

        # Check if payment is completed
        from payment.models import Payment
        payment = Payment.objects.filter(
            question=conversation.question,
            questioner=user,
            status='completed'
        ).first()

        if not payment:
            return HttpResponseForbidden("Payment required to access chat")

    elif user.role == "advisor":

        profile = get_object_or_404(
            AdvisorProfile,
            user=user,
        )

        if not QuestionAssignment.objects.filter(
            question=conversation.question,
            advisor=profile,
            status="accepted",
        ).exists():
            return HttpResponseForbidden("Access Denied")

    else:
        return HttpResponseForbidden("Access Denied")

    # Mark unread messages from the other user as read
    conversation.messages.filter(
        is_read=False
    ).exclude(
        sender=request.user
    ).update(
        is_read=True
    )

    # Close chat when the question is completed
    if conversation.question.status == "completed":

        return render(
            request,
            "chat/conversation_detail.html",
            {
                "conversation": conversation,
                "form": None,
                "chat_closed": True,
            },
        )

    if request.method == "POST":

        form = MessageForm(request.POST)

        if form.is_valid():

            message = form.save(commit=False)

            message.conversation = conversation

            message.sender = request.user

            message.save()

            return redirect(
                "conversation_detail",
                question_id=question_id,
            )

    else:

        form = MessageForm()

    return render(
        request,
        "chat/conversation_detail.html",
        {
            "conversation": conversation,
            "form": form,
            "chat_closed": False,
        },
    )


@login_required
def conversation_list(request):

    if request.user.role == "questioner":

        conversations = Conversation.objects.filter(
            question__questioner=request.user
        ).select_related(
            "question"
        ).annotate(
            unread_count=Count(
                "messages",
                filter=Q(
                    messages__is_read=False
                ) & ~Q(
                    messages__sender=request.user
                )
            )
        )

    elif request.user.role == "advisor":

        profile = get_object_or_404(
            AdvisorProfile,
            user=request.user
        )

        conversations = Conversation.objects.filter(
            question__assignments__advisor=profile,
            question__assignments__status="accepted"
        ).select_related(
            "question"
        ).annotate(
            unread_count=Count(
                "messages",
                filter=Q(
                    messages__is_read=False
                ) & ~Q(
                    messages__sender=request.user
                )
            )
        ).distinct()

    else:

        conversations = Conversation.objects.none()

    return render(
        request,
        "chat/conversation_list.html",
        {
            "conversations": conversations,
        },
    )


@login_required
@require_POST
def send_message_ajax(request, question_id):
    """Send message via AJAX without page refresh"""
    from question.models import Question
    question = get_object_or_404(Question, id=question_id)

    conversation, created = Conversation.objects.get_or_create(
        question=question
    )

    user = request.user

    # Access control
    if user.role == "questioner":
        if conversation.question.questioner != user:
            return JsonResponse({'success': False, 'error': 'Access Denied'}, status=403)
        # Check if payment is completed for questioners
        from payment.models import Payment
        payment = Payment.objects.filter(
            question=conversation.question,
            questioner=user,
            status='completed'
        ).first()
        if not payment:
            return JsonResponse({'success': False, 'error': 'Payment required to access chat'}, status=403)
    elif user.role == "advisor":
        profile = get_object_or_404(AdvisorProfile, user=user)
        if not QuestionAssignment.objects.filter(
            question=conversation.question,
            advisor=profile,
            status="accepted",
        ).exists():
            return JsonResponse({'success': False, 'error': 'Access Denied'}, status=403)
    else:
        return JsonResponse({'success': False, 'error': 'Access Denied'}, status=403)

    # Check if chat is closed
    if conversation.question.status == "completed":
        return JsonResponse({'success': False, 'error': 'Chat is closed'}, status=400)

    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()

        if not content:
            return JsonResponse({'success': False, 'error': 'Message cannot be empty'}, status=400)

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )

        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sender': message.sender.username,
                'sender_id': message.sender.id,
                'is_current_user': message.sender == request.user,
                'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_read': message.is_read
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)


@login_required
def get_new_messages_ajax(request, question_id):
    """Get new messages via AJAX for auto-refresh"""
    from question.models import Question
    question = get_object_or_404(Question, id=question_id)

    conversation, created = Conversation.objects.get_or_create(
        question=question
    )

    user = request.user

    # Access control
    if user.role == "questioner":
        if conversation.question.questioner != user:
            return JsonResponse({'success': False, 'error': 'Access Denied'}, status=403)
        # Check if payment is completed for questioners
        from payment.models import Payment
        payment = Payment.objects.filter(
            question=conversation.question,
            questioner=user,
            status='completed'
        ).first()
        if not payment:
            return JsonResponse({'success': False, 'error': 'Payment required to access chat'}, status=403)
    elif user.role == "advisor":
        profile = get_object_or_404(AdvisorProfile, user=user)
        if not QuestionAssignment.objects.filter(
            question=conversation.question,
            advisor=profile,
            status="accepted",
        ).exists():
            return JsonResponse({'success': False, 'error': 'Access Denied'}, status=403)
    else:
        return JsonResponse({'success': False, 'error': 'Access Denied'}, status=403)

    # Get the timestamp of the last message the client has
    last_message_id = request.GET.get('last_message_id', 0)

    # Get messages newer than the last one
    new_messages = conversation.messages.filter(
        id__gt=last_message_id
    ).order_by('created_at')

    # Mark unread messages from the other user as read
    conversation.messages.filter(
        is_read=False
    ).exclude(
        sender=request.user
    ).update(
        is_read=True
    )

    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'sender': msg.sender.username,
        'sender_id': msg.sender.id,
        'is_current_user': msg.sender == request.user,
        'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'is_read': msg.is_read
    } for msg in new_messages]

    return JsonResponse({
        'success': True,
        'messages': messages_data,
        'chat_closed': conversation.question.status == "completed"
    })