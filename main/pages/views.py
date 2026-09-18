from django.shortcuts import render


def home(request):
    return render(request, "home.html")

# Create your views here.
def register_choice(request):
    return render(request, "accounts/register_choice.html")