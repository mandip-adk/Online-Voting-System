from django.shortcuts import render, redirect
from .models import Election, Candidate, VoterParticipation, Votes
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.db.models import Count

@login_required
def election_list(request):
    
    elections =Election.objects.filter(status = 'active')
    return render (request, 'voting/election_list.html', {'elections': elections})


@login_required
def election_details(request, pk):

    election = get_object_or_404(Election, pk=pk)
    candidates = Candidate.objects.filter(election=election)
    return render (request, "voting/election_detail.html", {'election':election, 'candidates': candidates})


@login_required
def cast_vote(request, pk):
    election = get_object_or_404(Election, pk=pk)
    already_voted = VoterParticipation.objects.filter(
            user = request.user,
            election = election
        ).exists()
    if request.method == 'POST':
        candidate_id = request.POST.get('candidate_id')
        candidate = get_object_or_404(Candidate, pk=candidate_id)
        
        if already_voted:
            messages.error (request, "You have already cast your vote in this election.")
            return redirect ("result")
        else:
            Votes.objects.create(election=election, candidate=candidate)
            VoterParticipation.objects.create(user=request.user , election=election)
            return redirect ("result")
    else:
        candidates = election.candidates.all()
        return render(request, "voting/cast_vote.html", { 'candidates': candidates, 'election': election})

@login_required
def election_result(request, pk):
    election = get_object_or_404(Election,pk=pk)
    candidates = Candidate.objects.filter(election=election). annotate(
        vote_count = Count('votes')
    )   
    return render(request, "voting/result.html", {'election': election, 'candidates': candidates})
