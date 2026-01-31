from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .models import Election, Profile
from django.utils import timezone


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
    total_voters = User.objects.filter(profile__role= "voter").count()
    total_candidates = User.objects.filter(profile__role="candidate").count()

    active_election = Election.objects.filter(
        start_date__lte = timezone.now(),
        end_date__gte = timezone.now()
    ).first()

    election_status = "Active" if active_election else "Inactive"

    return render(request, "dashboard/admin.html", {
        "total_voters": total_voters,
        "total_candidate": total_candidates,
        "election_status": election_status,
        "active_election": active_election,

    })


@staff_member_required
def admin_voters(request):
    voters = Profile.objects.filter(role="voter").select_related("user")
    return render(request, "dashboard/admin_voters.html", {
        "voters": voters
    })

@staff_member_required
def admin_candidates(request):
    candidates = User.objects.filter(profile__role="candidate")
    return render(request, "dashboard/admin_candidates.html", {
        "candidates":candidates
    })

@staff_member_required
def admin_elections(request):
    elections = Election.objects.all()
    return render(request, "dashboard/admin_elections.html",{
        "elections": elections
    })

@staff_member_required
def admin_results(request):
    return render(request, "dashboard/admin_results.html")

@staff_member_required
def approve_voter(request, profile_id):
    profile = Profile.objects.get(id=profile_id)
    profile.is_approved = True
    profile.save()
    return redirect("admin_voters")

@staff_member_required
def block_voter(request, profile_id):
    profile = Profile.objects.get(id=profile_id)
    profile.is_approved = False
    profile.save()
    return redirect("admin_voters") 

def logout_view(request):
    logout(request)
    return redirect("login")


