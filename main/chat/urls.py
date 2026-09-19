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
    path(
        "conversation/<int:question_id>/send/",
        views.send_message_ajax,
        name="send_message_ajax",
    ),
    path(
        "conversation/<int:question_id>/get-new/",
        views.get_new_messages_ajax,
        name="get_new_messages_ajax",
    ),
]