from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.contrib import messages
from .models import QuestionerProfile
from .forms import QuestionerProfileForm, UserProfileForm
from question.models import Question
from review.models import Review
from accounts.models import CustomUser


@login_required
def dashboard(request):

    if request.user.role != "questioner":
        return HttpResponseForbidden("Access Denied")

    # Get or create questioner profile
    profile, created = QuestionerProfile.objects.get_or_create(
        user=request.user
    )

    # Get question statistics
    questions = Question.objects.filter(questioner=request.user)
    total_questions = questions.count()
    pending_questions = questions.filter(status='pending').count()
    accepted_questions = questions.filter(status='accepted').count()
    completed_questions = questions.filter(status='completed').count()

    # Get recent questions
    recent_questions = questions.select_related(
        'category'
    ).order_by('-created_at')[:5]

    # Get reviews submitted by this questioner
    reviews = Review.objects.filter(
        questioner=request.user
    ).select_related(
        'question',
        'advisor',
        'advisor__user'
    ).order_by('-created_at')[:5]
    
    # Get completed questions that don't have reviews yet for quick review submission
    completed_without_review = questions.filter(
        status='completed'
    ).exclude(
        id__in=Review.objects.filter(questioner=request.user).values_list('question_id', flat=True)
    ).select_related('category').prefetch_related('assignments__advisor').order_by('-created_at')[:5]

    return render(
        request,
        "questioner/dashboard.html",
        {
            "profile": profile,
            "total_questions": total_questions,
            "pending_questions": pending_questions,
            "accepted_questions": accepted_questions,
            "completed_questions": completed_questions,
            "recent_questions": recent_questions,
            "reviews": reviews,
            "completed_without_review": completed_without_review,
        },
    )


@login_required
def edit_questioner_profile(request):

    if request.user.role != "questioner":
        return HttpResponseForbidden("Access Denied")

    profile, created = QuestionerProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        profile_form = QuestionerProfileForm(
            request.POST,
            instance=profile,
        )

        user_form = UserProfileForm(
            request.POST,
            instance=request.user,
        )

        if profile_form.is_valid() and user_form.is_valid():

            profile_form.save()
            user_form.save()

            messages.success(
                request,
                "Profile updated successfully."
            )

            return redirect("questioner_dashboard")

    else:

        profile_form = QuestionerProfileForm(
            instance=profile,
        )

        user_form = UserProfileForm(
            instance=request.user,
        )

    return render(
        request,
        "questioner/edit_profile.html",
        {
            "profile_form": profile_form,
            "user_form": user_form,
        },
    )


@login_required
def questioner_profile_view(request):
    """Public view of a questioner's profile"""
    if request.user.role != "questioner":
        return HttpResponseForbidden("Access Denied")

    profile, created = QuestionerProfile.objects.get_or_create(
        user=request.user
    )

    # Get question statistics
    questions = Question.objects.filter(questioner=request.user)
    total_questions = questions.count()
    completed_questions = questions.filter(status='completed').count()

    # Get reviews submitted by this questioner
    reviews = Review.objects.filter(
        questioner=request.user
    ).select_related(
        'question',
        'advisor',
        'advisor__user',
        'question__category'
    ).order_by('-created_at')

    return render(
        request,
        'questioner/questioner_profile.html',
        {
            'profile': profile,
            'total_questions': total_questions,
            'completed_questions': completed_questions,
            'reviews': reviews,
        }
    )