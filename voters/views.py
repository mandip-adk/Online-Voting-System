from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

def login_page(request):
    if request.method == "POST":
        identifier = request.POST.get("email")  # email OR username
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=identifier,
            password=password
        )

        # If username login fails, try email
        if user is None:
            try:
                user_obj = User.objects.get(email=identifier)
                user = authenticate(
                    request,
                    username=user_obj.username,
                    password=password
                )
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        return render(
            request,
            "voters/login.html",
            {"error": "Invalid email or password"},
        )

    return render(request, "voters/login.html")



@login_required
def dashboard(request):
    user = request.user

    if user.is_superuser:
        return render(request, "dashboard/admin.html")
    if user.profile.role == "candidate":
        return render(request, "dashboard/candidate.html")
    
    return render(request, "dashboard/voter.html")


def register(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
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


