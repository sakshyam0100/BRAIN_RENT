from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Avg
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime
from notification.utils import notify_question_accepted, notify_answer_submitted, notify_new_question

from advisor.models import AdvisorProfile
from .models import Question, QuestionAssignment, Answer, Category
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

            # Notify advisors about new question
            notify_new_question(question)

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
    ).select_related(
        'category'
    ).prefetch_related(
        'assignments__advisor'
    ).order_by("-created_at")
    
    # Get payment information for each question
    from payment.models import Payment
    payments = Payment.objects.filter(
        question__in=questions
    ).select_related('advisor__user')
    
    # Create a mapping of question_id to payment
    payment_map = {payment.question.id: payment for payment in payments}
    
    # Attach payment to each question
    for question in questions:
        if question.id in payment_map:
            question.payment = payment_map[question.id]
        else:
            question.payment = None

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

    # Get payment status
    from payment.models import Payment
    payment = Payment.objects.filter(question=question).order_by('-created_at').first()

    return render(
        request,
        "question/question_detail.html",
        {
            "question": question,
            "assignment": assignment,
            "has_review": has_review,
            "average_rating": average_rating,
            "total_reviews": total_reviews,
            "payment": payment,
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
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    sort_by = request.GET.get("sort", "newest")

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

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
            questions = questions.filter(created_at__gte=date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
            questions = questions.filter(created_at__lte=date_to_obj)
        except ValueError:
            pass

    # Sorting options
    sort_options = {
        "newest": "-created_at",
        "oldest": "created_at",
        "title_asc": "title",
        "title_desc": "-title",
    }
    
    questions = questions.order_by(sort_options.get(sort_by, "-created_at"))

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(questions, 10)  # Show 10 questions per page
    
    try:
        questions = paginator.page(page)
    except PageNotAnInteger:
        questions = paginator.page(1)
    except EmptyPage:
        questions = paginator.page(paginator.num_pages)

    # Get all categories for the dropdown
    categories = Category.objects.all()

    # Build query parameters for pagination links
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    
    return render(
        request,
        "question/available_questions.html",
        {
            "questions": questions,
            "search_query": search_query,
            "category_filter": category_filter,
            "date_from": date_from,
            "date_to": date_to,
            "sort_by": sort_by,
            "categories": categories,
            "paginator": paginator,
            "query_params": query_params,
        },
    )


@login_required
def available_question_detail(request, question_id):
    """View details of an available (pending) question before accepting"""
    if request.user.role != "advisor":
        return HttpResponseForbidden("Access Denied")

    profile = AdvisorProfile.objects.filter(
        user=request.user
    ).first()

    if not profile or profile.verification_status != "approved":
        return HttpResponseForbidden(
            "Your advisor account is not approved yet."
        )

    question = get_object_or_404(
        Question,
        id=question_id,
        status="pending",
    )

    return render(
        request,
        "question/available_question_detail.html",
        {
            "question": question,
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

    # Notify questioner that their question was accepted
    notify_question_accepted(question, profile)

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
        "question__questioner"
    ).prefetch_related(
        "question__assignments__advisor"
    ).order_by("-assigned_at")
    
    # Get payment information for the questions
    from payment.models import Payment
    question_ids = [assignment.question.id for assignment in assignments]
    payments = Payment.objects.filter(
        question__id__in=question_ids
    ).select_related('questioner', 'advisor__user')
    
    # Create a mapping of question_id to payment
    payment_map = {payment.question.id: payment for payment in payments}
    
    # Attach payment to each assignment's question
    for assignment in assignments:
        if assignment.question.id in payment_map:
            assignment.question.payment = payment_map[assignment.question.id]
        else:
            assignment.question.payment = None

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

    # Check if question has a review
    from review.models import Review
    review = Review.objects.filter(
        question=assignment.question
    ).select_related('questioner').first()

    return render(
        request,
        "question/advisor_question_detail.html",
        {
            "assignment": assignment,
            "has_answer": has_answer,
            "review": review,
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

            # Notify questioner that answer was submitted
            notify_answer_submitted(question, profile)

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