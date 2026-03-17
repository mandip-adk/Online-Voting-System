from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages

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
