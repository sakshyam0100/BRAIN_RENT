from django.urls import path

from . import views

urlpatterns = [

    path(
        "questions/<int:question_id>/review/",
        views.submit_review,
        name="submit_review",
    ),
    path(
        "reviews/<int:review_id>/edit/",
        views.edit_review,
        name="edit_review",
    ),
    path(
        "reviews/<int:review_id>/delete/",
        views.delete_review,
        name="delete_review",
    ),
    path(
        "my-reviews/",
        views.my_reviews,
        name="my_reviews",
    ),

]