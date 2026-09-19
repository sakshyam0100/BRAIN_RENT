from django.urls import path
from . import views

urlpatterns = [
    path(
        "dashboard/questioner/",
        views.dashboard,
        name="questioner_dashboard",
    ),
    path(
        "profile/questioner/edit/",
        views.edit_questioner_profile,
        name="edit_questioner_profile",
    ),
    path(
        "profile/questioner/",
        views.questioner_profile_view,
        name="questioner_profile_view",
    ),
]