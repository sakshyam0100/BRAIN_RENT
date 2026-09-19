from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render,get_object_or_404
from django.db.models import Avg, Count, Sum
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import AdvisorProfile
from review.models import Review
from payment.models import Payment
from .forms import AdvisorProfileForm, AdvisorVerificationForm, UserProfileForm


@login_required
def advisor_verification(request):

    if request.user.role != "advisor":
        return HttpResponseForbidden("Access Denied")

    if request.method == "POST":

        profile_form = AdvisorProfileForm(request.POST)

        verification_form = AdvisorVerificationForm(
            request.POST,
            request.FILES,
        )

        if profile_form.is_valid() and verification_form.is_valid():

            profile = profile_form.save(commit=False)
            profile.user = request.user
            profile.save()

            profile_form.save_m2m()

            verification = verification_form.save(commit=False)
            verification.advisor = profile
            verification.save()

            return redirect("advisor_dashboard")

    else:

        profile_form = AdvisorProfileForm()
        verification_form = AdvisorVerificationForm()

    return render(
        request,
        "advisor/verification.html",
        {
            "profile_form": profile_form,
            "verification_form": verification_form,
        },
    )


@login_required
def advisor_dashboard(request):

    if request.user.role != "advisor":
        return HttpResponseForbidden("Access Denied")

    profile = AdvisorProfile.objects.filter(
        user=request.user
    ).first()

    reviews = Review.objects.filter(
        advisor=profile
    ).select_related(
        "question",
        "questioner",
    ).order_by("-created_at")

    average_rating = reviews.aggregate(
        Avg("rating")
    )["rating__avg"]
    
    # Get earnings data
    completed_payments = Payment.objects.filter(
        advisor=profile,
        status='completed'
    ).select_related('question', 'questioner')
    
    total_earnings = completed_payments.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Get this month's earnings
    now = timezone.now()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_earnings = completed_payments.filter(
        completed_at__gte=this_month_start
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Get this week's earnings
    this_week_start = now - timedelta(days=now.weekday())
    this_week_start = this_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    weekly_earnings = completed_payments.filter(
        completed_at__gte=this_week_start
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Get recent earnings
    recent_earnings = completed_payments.order_by('-completed_at')[:5]
    
    # Get payment count
    total_payments = completed_payments.count()
    pending_payments = Payment.objects.filter(
        advisor=profile,
        status='pending'
    ).count()

    return render(
        request,
        "advisor/dashboard.html",
        {
            "profile": profile,
            "reviews": reviews,
            "average_rating": average_rating,
            "total_earnings": total_earnings,
            "monthly_earnings": monthly_earnings,
            "weekly_earnings": weekly_earnings,
            "recent_earnings": recent_earnings,
            "total_payments": total_payments,
            "pending_payments": pending_payments,
        },
    )

@login_required
def edit_advisor_profile(request):

    if request.user.role != "advisor":
        return HttpResponseForbidden("Access Denied")

    profile = get_object_or_404(
        AdvisorProfile,
        user=request.user,
    )

    if request.method == "POST":

        profile_form = AdvisorProfileForm(
            request.POST,
            instance=profile,
        )

        user_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )

        if profile_form.is_valid() and user_form.is_valid():

            profile_form.save()
            user_form.save()

            messages.success(
                request,
                "Profile updated successfully."
            )

            return redirect("advisor_dashboard")

    else:

        profile_form = AdvisorProfileForm(
            instance=profile,
        )

        user_form = UserProfileForm(
            instance=request.user,
        )

    return render(
        request,
        "advisor/edit_profile.html",
        {
            "profile_form": profile_form,
            "user_form": user_form,
        },
    )


def advisor_profile_view(request, advisor_id):
    """Public view of an advisor's profile"""
    advisor = get_object_or_404(
        AdvisorProfile,
        id=advisor_id,
        verification_status='approved'
    )
    
    # Get reviews with related data
    reviews = Review.objects.filter(
        advisor=advisor
    ).select_related(
        'question',
        'questioner',
        'question__category'
    ).order_by('-created_at')
    
    # Calculate rating statistics
    rating_stats = reviews.aggregate(
        average_rating=Avg('rating'),
        total_reviews=Count('id')
    )
    
    average_rating = rating_stats['average_rating'] or 0
    total_reviews = rating_stats['total_reviews'] or 0
    
    # Calculate rating distribution with percentages
    rating_distribution = {}
    for i in range(1, 6):
        count = reviews.filter(rating=i).count()
        percentage = (count / total_reviews * 100) if total_reviews > 0 and count > 0 else 0
        rating_distribution[str(i)] = {
            'count': count,
            'percentage': percentage
        }
    
    # Get recent questions assigned to this advisor
    from question.models import QuestionAssignment
    recent_assignments = QuestionAssignment.objects.filter(
        advisor=advisor,
        status='accepted'
    ).select_related(
        'question',
        'question__category'
    ).order_by('-assigned_at')[:5]
    
    # Calculate completion rate
    total_assignments = QuestionAssignment.objects.filter(advisor=advisor).count()
    completed_assignments = QuestionAssignment.objects.filter(
        advisor=advisor,
        status='completed'
    ).count()
    completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
    
    return render(
        request,
        'advisor/advisor_profile.html',
        {
            'advisor': advisor,
            'reviews': reviews,
            'average_rating': average_rating,
            'total_reviews': total_reviews,
            'rating_distribution': rating_distribution,
            'recent_assignments': recent_assignments,
            'completion_rate': completion_rate,
        }
    )