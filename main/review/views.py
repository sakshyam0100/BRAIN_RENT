from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from advisor.models import AdvisorProfile
from question.models import Question
from .forms import ReviewForm
from .models import Review


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