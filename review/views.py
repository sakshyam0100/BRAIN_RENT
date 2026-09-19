from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from advisor.models import AdvisorProfile
from question.models import Question
from .forms import ReviewForm
from .models import Review
from notification.utils import notify_review_received


@login_required
def submit_review(request, question_id):

    if request.user.role != "questioner":
        return HttpResponseForbidden("Access Denied")

    question = get_object_or_404(
        Question,
        id=question_id,
        questioner=request.user,
        status="completed",
    )

    if hasattr(question, "review"):
        return HttpResponseForbidden(
            "You have already reviewed this question."
        )

    advisor = get_object_or_404(
        AdvisorProfile,
        assignments__question=question,
        assignments__status="accepted",
    )

    if request.method == "POST":

        form = ReviewForm(request.POST)

        if form.is_valid():

            review = form.save(commit=False)

            review.question = question

            review.questioner = request.user

            review.advisor = advisor

            review.save()

            # Notify advisor about the new review
            notify_review_received(review)

            return redirect(
                "question_detail",
                question_id=question.id,
            )

    else:

        form = ReviewForm()

    return render(
        request,
        "review/submit_review.html",
        {
            "form": form,
            "question": question,
        },
    )


@login_required
def edit_review(request, review_id):
    """Edit an existing review"""
    review = get_object_or_404(
        Review,
        id=review_id,
        questioner=request.user
    )

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Your review has been updated successfully.")
            return redirect("question_detail", question_id=review.question.id)
    else:
        form = ReviewForm(instance=review)

    return render(
        request,
        "review/edit_review.html",
        {
            "form": form,
            "review": review,
            "question": review.question,
        },
    )


@login_required
def delete_review(request, review_id):
    """Delete an existing review"""
    review = get_object_or_404(
        Review,
        id=review_id,
        questioner=request.user
    )

    question_id = review.question.id

    if request.method == "POST":
        review.delete()
        messages.success(request, "Your review has been deleted successfully.")
        return redirect("question_detail", question_id=question_id)

    return render(
        request,
        "review/delete_review.html",
        {
            "review": review,
            "question": review.question,
        },
    )


@login_required
def my_reviews(request):
    """View all reviews given by the current user (questioner)"""
    if request.user.role != "questioner":
        return HttpResponseForbidden("Access Denied")

    reviews = Review.objects.filter(
        questioner=request.user
    ).select_related(
        'advisor',
        'advisor__user',
        'question',
        'question__category'
    ).order_by('-created_at')

    return render(
        request,
        'review/my_reviews.html',
        {
            'reviews': reviews,
        }
    )