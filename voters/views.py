from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .models import Election


def login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")  # email OR username
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        # If username login fails, try email
        if user:
            login(request, user)

            if user.is_superuser:
                return redirect("admin_dashboard")
            else:
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


@staff_member_required
def admin_dashboard(request):
    elections = Election.objects.all()
    return render(request, "dashboard/admin.html", {
        "elections": elections
    })


def logout_view(request):
    logout(request)
    return redirect("login")


