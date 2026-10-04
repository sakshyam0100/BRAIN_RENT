from django.urls import path

from . import views

urlpatterns = [

    path(
        "questions/<int:question_id>/review/",
        views.submit_review,
        name="submit_review",
    ),

]