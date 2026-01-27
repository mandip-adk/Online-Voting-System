from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

def login_page(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(
                request, "voters/login.html", {"error":"Invalid email or password"}
            )
    return render(request, "voters/login.html")

def dashboard(request):
    return render(request, "voters/dashboard.html")
def register(request):
    if request.method == "POST":
        first_name = request.POST("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        return redirect("login")
    return render(request, "voters/register.html")


def logout_view(request):
    logout(request)
    return redirect("login")


