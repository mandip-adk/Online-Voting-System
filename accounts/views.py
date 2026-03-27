from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from voting.models import Election, VoterParticipation


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
        active_elections = Election.objects.filter(status='active')
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
            'complete_count': complete_count
            })
    else:
        return redirect('home')

