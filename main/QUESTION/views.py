from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Avg

from advisor.models import AdvisorProfile
from .models import Question, QuestionAssignment, Answer
from .forms import QuestionForm, AnswerForm
from chat.models import Conversation
from review.models import Review
from django.db.models import Q


@login_required
def ask_question(request):

    if request.user.role != "questioner":
        return HttpResponseForbidden("Access Denied")

    if request.method == "POST":

        form = QuestionForm(request.POST)

        if form.is_valid():

            question = form.save(commit=False)
            question.questioner = request.user
            question.save()

            return redirect("my_questions")

    else:

        form = QuestionForm()

    return render(
        request,
        "question/ask_question.html",
        {
            "form": form,
        },
    )


@login_required
def my_questions(request):

    if request.user.role != "questioner":
        return HttpResponseForbidden("Access Denied")

    questions = Question.objects.filter(
        questioner=request.user
    ).order_by("-created_at")

    return render(
        request,
        "question/my_questions.html",
        {
            "questions": questions,
        },
    )


@login_required
def question_detail(request, question_id):

    if request.user.role != "questioner":
        return HttpResponseForbidden("Access Denied")

    question = get_object_or_404(
        Question,
        id=question_id,
        questioner=request.user,
    )

    assignment = QuestionAssignment.objects.filter(
        question=question,
        status="accepted",
    ).select_related(
        "advisor",
        "advisor__user",
    ).first()

    has_review = Review.objects.filter(
        question=question
    ).exists()

    average_rating = None
    total_reviews = 0

    if assignment:

        advisor_reviews = Review.objects.filter(
            advisor=assignment.advisor
        )

        average_rating = advisor_reviews.aggregate(
            Avg("rating")
        )["rating__avg"]

        total_reviews = advisor_reviews.count()

    return render(
        request,
        "question/question_detail.html",
        {
            "question": question,
            "assignment": assignment,
            "has_review": has_review,
            "average_rating": average_rating,
            "total_reviews": total_reviews,
        },
    )


@login_required
def available_questions(request):
    if request.user.role != "advisor":
        return HttpResponseForbidden("Access Denied")

    profile = AdvisorProfile.objects.filter(
        user=request.user
    ).first()

    if not profile or profile.verification_status != "approved":
        return HttpResponseForbidden(
            "Your advisor account is not approved yet."
        )

    search_query = request.GET.get("q", "").strip()
    category_filter = request.GET.get("category", "").strip()

    questions = Question.objects.filter(
        status="pending"
    ).select_related(
        "category",
        "questioner"
    )

    if search_query:
        questions = questions.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if category_filter:
        questions = questions.filter(
            category__name__icontains=category_filter
        )

    questions = questions.order_by("-created_at")

    return render(
        request,
        "question/available_questions.html",
        {
            "questions": questions,
            "search_query": search_query,
            "category_filter": category_filter,
        },
    )


@login_required
def accept_question(request, question_id):

    if request.user.role != "advisor":
        return HttpResponseForbidden("Access Denied")

    profile = get_object_or_404(
        AdvisorProfile,
        user=request.user,
        verification_status="approved",
    )

    question = get_object_or_404(
        Question,
        id=question_id,
        status="pending",
    )

    QuestionAssignment.objects.create(
        question=question,
        advisor=profile,
        status="accepted",
    )

    question.status = "accepted"
    question.save()

    Conversation.objects.get_or_create(
        question=question,
    )

    return redirect("assigned_questions")


@login_required
def assigned_questions(request):

    if request.user.role != "advisor":
        return HttpResponseForbidden("Access Denied")

    profile = get_object_or_404(
        AdvisorProfile,
        user=request.user,
    )

    assignments = QuestionAssignment.objects.filter(
        advisor=profile
    ).select_related(
        "question",
        "question__category",
        "question__questioner",
    ).order_by("-assigned_at")

    return render(
        request,
        "question/assigned_questions.html",
        {
            "assignments": assignments,
        },
    )


@login_required
def advisor_question_detail(request, question_id):

    if request.user.role != "advisor":
        return HttpResponseForbidden("Access Denied")

    profile = get_object_or_404(
        AdvisorProfile,
        user=request.user,
    )

    assignment = get_object_or_404(
        QuestionAssignment,
        advisor=profile,
        question_id=question_id,
    )

    has_answer = Answer.objects.filter(
        question=assignment.question
    ).exists()

    return render(
        request,
        "question/advisor_question_detail.html",
        {
            "assignment": assignment,
            "has_answer": has_answer,
        },
    )


@login_required
def submit_answer(request, question_id):

    if request.user.role != "advisor":
        return HttpResponseForbidden("Access Denied")

    profile = get_object_or_404(
        AdvisorProfile,
        user=request.user,
        verification_status="approved"
    )

    question = get_object_or_404(
        Question,
        id=question_id
    )

    if not QuestionAssignment.objects.filter(
        question=question,
        advisor=profile,
        status="accepted"
    ).exists():
        return HttpResponseForbidden("Access Denied")

    if hasattr(question, "answer"):
        return HttpResponseForbidden(
            "This question already has an answer."
        )

    if request.method == "POST":

        form = AnswerForm(request.POST)

        if form.is_valid():

            answer = form.save(commit=False)

            answer.question = question
            answer.advisor = profile

            answer.save()

            question.status = "completed"
            question.save()

            return redirect(
                "advisor_question_detail",
                question_id=question.id
            )

    else:

        form = AnswerForm()

    return render(
        request,
        "question/submit_answer.html",
        {
            "form": form,
            "question": question,
        },
    )