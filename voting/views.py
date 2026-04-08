from django.shortcuts import render, redirect
from .models import Election, Candidate, VoterParticipation, Votes
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.db.models import Count
from accounts.models import CustomUser
from django.utils import timezone

@login_required
def election_list(request):
    election = Election.objects.all()

    for election in elections:
        election.sync_status()

    elections =Election.objects.all()
    return render (request, 'voting/election_list.html', {
        'elections': elections,
        'active_count': elections.filter(status='active').count(),
        'pending_count': elections.filter(status='pending').count(),
        'closed_count': elections.filter(status='closed').count(),
        })


@login_required
def election_details(request, pk):
    election = get_object_or_404(Election, pk=pk)
    election.sync_status()
    candidates = Candidate.objects.filter(election=election)
    has_voted = VoterParticipation.objects.filter( 
        user=request.user,
        election=election
    ).exists()
    return render(request, "voting/election_detail.html", {
        'election': election,
        'candidates': candidates,
        'has_voted': has_voted,  
    })

@login_required
def cast_vote(request, pk):
    election = get_object_or_404(Election, pk=pk)
    election.sync_status()

    # block if election isn't active
    if election.status != 'active':
        messages.error(request, "This election is not currently active.")
        return redirect('voting:election_detail', pk=pk)

    already_voted = VoterParticipation.objects.filter(
        user=request.user,
        election=election
    ).exists()

    # block if already voted before even processing POST
    if already_voted:
        messages.error(request, "You have already cast your vote in this election.")
        return redirect('voting:result', pk=pk)

    if request.method == 'POST':
        candidate_id = request.POST.get('candidate')
        candidate = get_object_or_404(Candidate, pk=candidate_id, election=election)

        Votes.objects.create(
            election=election,
            candidate=candidate,
            voted_at=timezone.now()
        )
        VoterParticipation.objects.create(
            user=request.user,
            election=election,
            voted_at=timezone.now()
        )
        messages.success(request, "Your vote has been cast successfully! 🎉")
        return redirect('voting:result', pk=pk)

    else:
        candidates = election.candidates.all()
        return render(request, "voting/cast_vote.html", {
            'candidates': candidates,
            'election':   election,
        })
@login_required
def election_result(request, pk):
    election = get_object_or_404(Election, pk=pk)

    candidates = Candidate.objects.filter(election=election)\
        .annotate(vote_count=Count('votes'))\
        .order_by('-vote_count')

    total_votes      = election.votes.count()
    total_registered = CustomUser.objects.filter(role='voter').count()
    participated     = election.participations.count()

    # ── Fix 1: correct turnout calculation ──
    turnout_pct = round(participated / total_registered * 100) \
                  if total_registered > 0 else 0

    # ── Fix 2: attach percentage to each candidate ──
    candidates_with_pct = []
    for candidate in candidates:
        candidate.percentage = round(
            candidate.vote_count / total_votes * 100, 1
        ) if total_votes > 0 else 0
        candidates_with_pct.append(candidate)

    winner = candidates_with_pct[0] if candidates_with_pct else None

    recent_participations = VoterParticipation.objects\
        .filter(election=election)\
        .order_by('-voted_at')[:5]

    return render(request, "voting/result.html", {
        'election':              election,
        'candidates':            candidates_with_pct,
        'total_votes':           total_votes,
        'total_registered':      total_registered,
        'turnout_pct':           turnout_pct,
        'recent_participations': recent_participations,
        'winner':                winner,
    })