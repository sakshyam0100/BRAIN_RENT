from django.urls import path
from . import views

urlpatterns = [
    path(
        "advisor/verification/",
        views.advisor_verification,
        name="advisor_verification",
    ),
    path(
    "dashboard/advisor/",
    views.advisor_dashboard,
    name="advisor_dashboard",
    ),
    path(
    "advisor/profile/edit/",
    views.edit_advisor_profile,
    name="edit_advisor_profile",
    ),
]