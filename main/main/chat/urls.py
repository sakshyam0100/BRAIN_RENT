from django.urls import path
from . import views

urlpatterns = [

    path(
        "",
        views.conversation_list,
        name="conversation_list",
    ),
    path(
        "conversation/<int:question_id>/",
        views.conversation_detail,
        name="conversation_detail",
    ),
]