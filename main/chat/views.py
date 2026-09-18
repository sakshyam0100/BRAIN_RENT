from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Count, Q

from advisor.models import AdvisorProfile
from question.models import QuestionAssignment
from .models import Conversation
from .forms import MessageForm


@login_required
def conversation_detail(request, question_id):

    conversation = get_object_or_404(
        Conversation,
        question_id=question_id,
    )

    user = request.user

    if user.role == "questioner":

        if conversation.question.questioner != user:
            return HttpResponseForbidden("Access Denied")

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