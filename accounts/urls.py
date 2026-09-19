from django.urls import path
from . import views

urlpatterns = [
    path(
        "register/questioner/",
        views.questioner_register,
        name="questioner_register",
    ),

    path(
        "login/",
        views.login_view,
        name="login",
    ),
    path(
    "logout/",
    views.logout_view,
    name="logout",
   ),
   path(
    "register/advisor/",
    views.advisor_register,
    name="advisor_register",
   ),
]