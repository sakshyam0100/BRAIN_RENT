from django.urls import path
from . import views

urlpatterns = [
    path(
        "dashboard/questioner/",
        views.dashboard,
        name="questioner_dashboard",
    ),
]