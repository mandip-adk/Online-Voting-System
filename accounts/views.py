from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from voting.models import Election, VoterParticipation, Candidate, Votes
from .models import CustomUser
from django.db.models import Count
from audit.models import AuditRequest


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully.")
            return redirect('login')
        else:
            messages.error(request, "Invalid information. Please check and provide correct data.")
            return render(request, 'accounts/register.html', {'form': form})
    else:
        form = RegisterForm()
        return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_superuser:
                return redirect('/admin')
            elif user.role == 'organizer':
                return redirect('organizer_dashboard')
            else:
                return redirect('voter_dashboard')  # ← default fallback
        else:
            messages.error(request, "Invalid email/username or password.")
            return render(request, 'accounts/login.html', {'form': form})
    else:
        form = AuthenticationForm()
        return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def home(request):
    if request.user.is_authenticated:
        if request.user.role == 'organizer':
            return redirect('organizer_dashboard')
        else:
            return redirect('voter_dashboard')  # ← default fallback
    return render(request, 'home.html')


@login_required
def voter_dashboard(request):
    if request.user.role != 'voter':
        return redirect('home')

    elections = Election.objects.all()
    for election in elections:
        election.sync_status()

    elections = Election.objects.all()
    election_with_status = []
    voted_count = pending_count = completed_count = 0

    for election in elections:
        has_voted = VoterParticipation.objects.filter(
            user=request.user, election=election
        ).exists()
        has_applied = Candidate.objects.filter(
            user=request.user, election=election
        ).exists()

        # ── vote percentage per candidate ──────────────────────
        total_votes = Votes.objects.filter(election=election).count()
        candidates = election.candidates.filter(status='approved')
        for candidate in candidates:
            c_votes = Votes.objects.filter(candidate=candidate).count()
            candidate.vote_percentage = round(
                (c_votes / total_votes * 100) if total_votes > 0 else 0
            )
        # ───────────────────────────────────────────────────────

        election_with_status.append({
            'election':    election,
            'has_voted':   has_voted,
            'has_applied': has_applied,
        })

        if has_voted:
            voted_count += 1
        if election.status == 'active' and not has_voted:
            pending_count += 1
        if election.status == 'closed' and has_voted:
            completed_count += 1

    my_candidacies = Candidate.objects.filter(
        user=request.user
    ).select_related('election')

    candidacy_data = []
    for candidacy in my_candidacies:
        votes_received = Votes.objects.filter(candidate=candidacy).count()
        audit = AuditRequest.objects.filter(
            candidate=candidacy,
            election=candidacy.election
        ).first()
        candidacy_data.append({
            'election':       candidacy.election,
            'status':         candidacy.status,
            'votes_received': votes_received,
            'has_audit':      audit is not None,
            'audit_pk':       audit.pk if audit else None,
        })

    return render(request, 'voting/dashboard/voter_dashboard.html', {
        'election_with_status': election_with_status,
        'voted_count':          voted_count,
        'pending_count':        pending_count,
        'completed_count':      completed_count,
        'my_candidacies':       candidacy_data,
        'is_candidate':         my_candidacies.exists(),
    })


@login_required
def organizer_dashboard(request):
    if request.user.role != 'organizer':
        return redirect('home')

    # Only this organizer's elections
    elections = Election.objects.filter(created_by=request.user)
    for election in elections:
        election.sync_status()
    elections = Election.objects.filter(created_by=request.user)

    election_with_vote_count = []
    for election in elections:
        vote_count = Votes.objects.filter(election=election).count()
        election_with_vote_count.append({
            'election':   election,
            'vote_count': vote_count,
        })

    # Pending candidate applications for all organizer's elections
    pending_applications = Candidate.objects.filter(
        election__created_by=request.user,
        status='pending'
    ).select_related('user', 'election')

    return render(request, 'voting/dashboard/organizer_dashboard.html', {
        'total_elections':           elections.count(),
        'active_elections':          elections.filter(status='active').count(),
        'pending_elections':         elections.filter(status='pending').count(),
        'closed_elections':          elections.filter(status='closed').count(),
        'total_vote_cast':           Votes.objects.filter(election__created_by=request.user).count(),
        'election_with_vote_count':  election_with_vote_count,
        'pending_applications':      pending_applications,        # ← new
        'pending_applications_count': pending_applications.count(), # ← new
    })