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
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.is_superuser:
                return redirect('/admin')
            elif user.role == 'organizer':
                return redirect('organizer_dashboard')
            else:
                return redirect('voter_dashboard')
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
        if request.user.role == 'admin' or request.user.is_superuser:
            return redirect('admin_dashboard')
        elif request.user.role == 'organizer':
            return redirect('organizer_dashboard')
        else:
            return redirect('voter_dashboard')
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

        total_votes = Votes.objects.filter(election=election).count()
        candidates = election.candidates.filter(status='approved')
        for candidate in candidates:
            c_votes = Votes.objects.filter(candidate=candidate).count()
            candidate.vote_percentage = round(
                (c_votes / total_votes * 100) if total_votes > 0 else 0
            )

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

    pending_applications = Candidate.objects.filter(
        election__created_by=request.user,
        status='pending'
    ).select_related('user', 'election')

    return render(request, 'voting/dashboard/organizer_dashboard.html', {
        'total_elections':            elections.count(),
        'active_elections':           elections.filter(status='active').count(),
        'pending_elections':          elections.filter(status='pending').count(),
        'closed_elections':           elections.filter(status='closed').count(),
        'total_vote_cast':            Votes.objects.filter(election__created_by=request.user).count(),
        'election_with_vote_count':   election_with_vote_count,
        'pending_applications':       pending_applications,
        'pending_applications_count': pending_applications.count(),
    })


@login_required
def admin_dashboard(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')

    # Sync all election statuses
    for election in Election.objects.all():
        election.sync_status()

    # --- User stats ---
    total_users      = CustomUser.objects.filter(is_superuser=False).count()
    total_voters     = CustomUser.objects.filter(role='voter').count()
    total_organizers = CustomUser.objects.filter(role='organizer').count()
    total_admins     = CustomUser.objects.filter(role='admin').count()

    # --- Election stats ---
    all_elections    = Election.objects.all().order_by('start_date')
    active_elections  = all_elections.filter(status='active')
    pending_elections = all_elections.filter(status='pending')
    closed_elections  = all_elections.filter(status='closed')

    # --- Vote stats ---
    total_votes        = Votes.objects.count()
    total_participants = VoterParticipation.objects.count()

    # --- Candidate stats ---
    total_candidates          = Candidate.objects.count()
    pending_candidate_apps    = Candidate.objects.filter(status='pending').count()

    # --- Audit stats ---
    total_audits   = AuditRequest.objects.count()
    pending_audits = AuditRequest.objects.filter(status='pending').count()

    # --- Per-election vote breakdown (for table) ---
    elections_with_stats = []
    for election in all_elections:
        vote_count         = Votes.objects.filter(election=election).count()
        participant_count  = VoterParticipation.objects.filter(election=election).count()
        candidate_count    = Candidate.objects.filter(election=election, status='approved').count()
        elections_with_stats.append({
            'election':         election,
            'vote_count':       vote_count,
            'participant_count':participant_count,
            'candidate_count':  candidate_count,
        })

    # --- Recent users (last 10 registered) ---
    recent_users = CustomUser.objects.filter(
        is_superuser=False
    ).order_by('-date_joined')[:10]

    return render(request, 'voting/dashboard/admin_dashboard.html', {
        # user stats
        'total_users':             total_users,
        'total_voters':            total_voters,
        'total_organizers':        total_organizers,
        'total_admins':            total_admins,
        # election stats
        'total_elections':         all_elections.count(),
        'active_elections':        active_elections,
        'active_elections_count':  active_elections.count(),
        'pending_elections':       pending_elections,
        'pending_elections_count': pending_elections.count(),
        'closed_elections_count':  closed_elections.count(),
        # vote stats
        'total_votes':             total_votes,
        'total_participants':      total_participants,
        # candidate stats
        'total_candidates':        total_candidates,
        'pending_candidate_apps':  pending_candidate_apps,
        # audit stats
        'total_audits':            total_audits,
        'pending_audits':          pending_audits,
        # tables
        'elections_with_stats':    elections_with_stats,
        'recent_users':            recent_users,
    })

    