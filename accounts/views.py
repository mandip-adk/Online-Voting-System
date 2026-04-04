from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from voting.models import Election, VoterParticipation, Candidate, Votes
from .models import CustomUser
from django.db.models import Count


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.error(request, "Account created successfully. ")
            return redirect('login')
        else:
            messages.error(request, "Invalid information please check and provided correct data.")
            return render(request, 'accounts/register.html', {'form': form})
    else:
        form = RegisterForm()
        return render(request, 'accounts/register.html',{'form':form})
    
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            user = form.get_user()
            login (request, user )

            if user.role == 'voter':
                return redirect('voter_dashboard')
            elif user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'candidate':
                return redirect('candidate_dashboard')
        else:
            messages.error (request, "Invalid email/username or password.")
            return render(request, 'accounts/login.html',{'form':form}) 
               
    else:
        form = AuthenticationForm()
        return render(request, 'accounts/login.html', {'form':form})
    
def logout_view(request):
    logout(request)
    return redirect('login')

def home(request):
    return render(request, 'home.html')


@login_required
def voter_dashboard(request):
    if request.user.role == 'voter':
        active_elections = Election.objects.all()
        election_with_status= []
        voted_count = pending_count = complete_count = 0
    
        for election in active_elections:

            has_voted = VoterParticipation.objects.filter(
                user =request.user,
                election =election
                ).exists()
            election_with_status.append({'election': election,
                                        'has_voted': has_voted})
            
            if has_voted:
                voted_count += 1
            if election.status == 'active' and not has_voted:
                pending_count += 1
            if election.status == 'closed' and not has_voted:
                complete_count += 1

        return render(request, 'voting/dashboard/voter_dashboard.html', {
            'election_with_status': election_with_status,
            'voted_count': voted_count,
            'pending_count': pending_count,
            'completed_count': complete_count
            })
    else:
        return redirect('home')
    
@login_required
def candidate_dashboard(request):
    if request.user.role != 'candidate':
        return redirect('home')
    
    else:

        elections = Election.objects.filter(candidates__user =request.user )
        election_with_votes = []
        total_votes = 0
        for election in elections:
            candidate = Candidate.objects.get(user = request.user, election= election)

            votes_received = Votes.objects.filter(candidate=candidate).count()
            total_votes+= votes_received

            election_with_votes.append({
                'election':election,
                'votes_received': votes_received
            })
        return render(request, 'voting/dashboard/candidate_dashboard.html', {
            'election_with_votes': election_with_votes,
            'total_elections': elections.count(),
            'active_elections': elections.filter(status='active').count(),
            'closed_elections': elections.filter(status='closed').count(),
            'total_votes': total_votes,
        })

        
@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect ('home')
    else:
        total_user = CustomUser.objects.count()
        total_election = Election.objects.count()
        total_voters = CustomUser.objects.filter(role= 'voter').count()
        total_candidates = CustomUser.objects.filter(role='candidate').count()
        total_vote_cast = Votes.objects.count()
        elections = Election.objects.all()
        election_with_vote_count= []

        for election in elections:
            vote_count = Votes.objects.filter(election=election).count()
            election_with_vote_count.append({
                'election':election,
                'vote_count': vote_count
            })
        
        return render(request, 'voting/dashboard/admin_dashboard.html',{
            'total_user':total_user,
            'total_election':total_election,
            'total_voters':total_voters,
            'total_candidates': total_candidates,
            'total_vote_cast': total_vote_cast,
            'election_with_vote_count': election_with_vote_count,
        })




