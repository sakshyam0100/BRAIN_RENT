from django.shortcuts import render, redirect
from .forms import RegistrationForm
from .forms import LoginForm
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
def questioner_register(request):

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("questioner_register")
    else:
        form = RegistrationForm()

    context = {
        "form": form,
    }

    return render(
        request,
        "accounts/questioner_register.html",
        context,
    )

def advisor_register(request):

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            user.role = "advisor"

            user.save()

            return redirect("login")

    else:
        form = RegistrationForm()

    return render(
        request,
        "accounts/advisor_register.html",
        {
            "form": form,
        },
    )

def login_view(request):

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)

        if form.is_valid():

            user = form.get_user()

            login(request, user)

            if user.role == "questioner":
                return redirect("questioner_dashboard")
            elif user.role == "advisor":
               return redirect("advisor_dashboard")

    else:
        form = LoginForm()

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
        },
    )


def logout_view(request):
    logout(request)
    return redirect("home")