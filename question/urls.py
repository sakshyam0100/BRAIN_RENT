from django.urls import path
from . import views

urlpatterns = [
    path(
        "question/ask/",
        views.ask_question,
        name="ask_question",
    ),
    path(
    "questions/my/",
    views.my_questions,
    name="my_questions",
    ),
    path(
    "questions/<int:question_id>/",
    views.question_detail,
    name="question_detail",
    ),
    path(
    "advisor/questions/",
    views.available_questions,
    name="available_questions",
    ),
    path(
    "advisor/questions/<int:question_id>/accept/",
    views.accept_question,
    name="accept_question",
    ),
    path(
    "advisor/questions/<int:question_id>/detail/",
    views.available_question_detail,
    name="available_question_detail",
    ),
    path(
    "advisor/assigned/",
    views.assigned_questions,
    name="assigned_questions",
    ),
    path(
    "questions/<int:question_id>/answer/",
    views.submit_answer,
    name="submit_answer",
    ),

    path(
    "advisor/questions/<int:question_id>/",
    views.advisor_question_detail,
    name="advisor_question_detail",
    ),
]