from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Election, Contest, ContestCandidate, ElectoralRoll, Vote


@login_required
def election_list(request):
    elections = Election.objects.filter(created_by=request.user).order_by('-start_date')
    for e in elections:
        e.sync_status()
    elections = Election.objects.filter(created_by=request.user).order_by('-start_date')
    return render(request, 'voting/election_list.html', {'elections': elections})


@login_required
def election_detail(request, pk):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    election.sync_status()
    return render(request, 'voting/election_detail.html', {'election': election})


@login_required
def create_election(request):
    return render(request, 'voting/create_election.html')


@login_required
def edit_election(request, pk):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    return render(request, 'voting/edit_election.html', {'election': election})


@login_required
def delete_election(request, pk):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    if request.method == 'POST':
        election.delete()
        messages.success(request, "Election deleted.")
        return redirect('voting:election_list')
    return render(request, 'voting/delete_election.html', {'election': election})


@login_required
def add_contest(request, pk):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    return render(request, 'voting/add_contest.html', {'election': election})


@login_required
def edit_contest(request, pk, ck):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    contest  = get_object_or_404(Contest, pk=ck, election=election)
    return render(request, 'voting/edit_contest.html', {'election': election, 'contest': contest})


@login_required
def delete_contest(request, pk, ck):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    contest  = get_object_or_404(Contest, pk=ck, election=election)
    if request.method == 'POST':
        contest.delete()
        messages.success(request, "Contest deleted.")
        return redirect('voting:election_detail', pk=pk)
    return render(request, 'voting/delete_contest.html', {'election': election, 'contest': contest})


@login_required
def upload_electoral_roll(request, pk):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    return render(request, 'voting/upload_electoral_roll.html', {'election': election})


@login_required
def voter_participation(request, pk):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    roll = election.electoral_roll.all().order_by('email')
    return render(request, 'voting/voter_participation.html', {
        'election': election,
        'roll':     roll,
    })


@login_required
def election_results(request, pk):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    return render(request, 'voting/election_results.html', {'election': election})


@login_required
def send_voting_emails(request, pk):
    election = get_object_or_404(Election, pk=pk, created_by=request.user)
    return render(request, 'voting/send_emails.html', {'election': election})


# ── Public ballot views (no login required) ───────────────────────────────────

def ballot(request, token):
    roll = get_object_or_404(ElectoralRoll, token=token)
    return render(request, 'voting/ballot.html', {'roll': roll})


def submit_vote(request, token):
    roll = get_object_or_404(ElectoralRoll, token=token)
    return render(request, 'voting/ballot.html', {'roll': roll})


def vote_receipt(request, token):
    roll = get_object_or_404(ElectoralRoll, token=token)
    return render(request, 'voting/vote_receipt.html', {'roll': roll})


