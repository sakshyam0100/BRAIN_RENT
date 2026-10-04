from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render,get_object_or_404
from django.db.models import Avg
from django.contrib import messages
from .models import AdvisorProfile
from review.models import Review
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

    return render(
        request,
        "advisor/dashboard.html",
        {
            "profile": profile,
            "reviews": reviews,
            "average_rating": average_rating,
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